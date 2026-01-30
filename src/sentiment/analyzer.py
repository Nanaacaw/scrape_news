"""
Sentiment Analysis Engine using IndoBERT
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Tuple, Optional
import numpy as np
import re

from src.utils.config import SENTIMENT_MODEL, SENTIMENT_BATCH_SIZE, SENTIMENT_MAX_LENGTH
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Keywords for heuristic adjustment
POSITIVE_KEYWORDS = {
    'melesat', 'terbang', 'cuan', 'laba', 'untung', 'naik', 'menguat', 
    'bullish', 'dividen', 'akuisisi', 'ekspansi', 'rekor', 'tumbuh', 
    'positif', 'optimis', 'hijau', 'buy', 'meningkat', 'profit'
}

NEGATIVE_KEYWORDS = {
    'anjlok', 'terjun', 'rugi', 'boncos', 'turun', 'melemah', 
    'bearish', 'bangkrut', 'pailit', 'utang', 'koreksi', 'negatif', 
    'pesimis', 'merah', 'sell', 'gagal', 'anjlog', 'longsor', 'merosot'
}

class SentimentAnalyzer:
    """
    Sentiment analyzer using IndoBERT pre-trained model
    
    Sentiment labels:
    - positive: score > 0.15 (adjusted from 0.3)
    - negative: score < -0.15 (adjusted from -0.3)
    - neutral: -0.15 <= score <= 0.15
    """
    
    def __init__(self, model_name: str = SENTIMENT_MODEL):
        """
        Initialize sentiment analyzer
        
        Args:
            model_name: HuggingFace model name or path
        """
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Loading sentiment model: {model_name}")
        logger.info(f"Using device: {self.device}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    "w11wo/indonesian-roberta-base-sentiment-classifier"
                )
                self.use_sentiment_head = True
                logger.info("Using dedicated sentiment classification model")
            except:
                logger.warning("Sentiment classifier not found, using IndoBERT base model")
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=3
                )
                self.use_sentiment_head = False
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("Sentiment model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a single text with sliding window for long texts
        """
        return self._analyze_single_with_chunking(text)
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Analyze sentiment of multiple texts
        Now processes each text with chunking to ensure accuracy
        """
        results = []
        # Process sequentially to manage memory with chunking
        # (A single long article might spawn multiple chunks)
        for text in texts:
            try:
                res = self._analyze_single_with_chunking(text)
                results.append(res)
            except Exception as e:
                logger.error(f"Error analyzing text: {e}")
                results.append({
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0
                })
        return results
    
    def _analyze_single_with_chunking(self, text: str) -> Dict[str, float]:
        """
        Analyze a single text using sliding window approach
        """
        if not text:
            return {'sentiment_score': 0.0, 'sentiment_label': 'neutral', 'confidence': 0.0}

        # Tokenize with sliding window
        # stride=128 means 128 tokens overlap between chunks
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=SENTIMENT_MAX_LENGTH,
            return_overflowing_tokens=True,
            stride=128,
            return_tensors='pt'
        )
        
        # Remove overflow_to_sample_mapping if it exists (not needed for inference)
        if 'overflow_to_sample_mapping' in inputs:
            inputs.pop('overflow_to_sample_mapping')
            
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        probabilities = torch.softmax(logits, dim=-1)
        
        # Average probabilities across all chunks
        # This gives a "consensus" sentiment for the whole document
        avg_probs = torch.mean(probabilities, dim=0)
        
        prediction = torch.argmax(avg_probs).item()
        confidence = avg_probs[prediction].item()
        
        # Convert to score (-1 to 1)
        # 0=negative, 1=neutral, 2=positive
        # Score = Prob(Pos) - Prob(Neg)
        sentiment_score = avg_probs[2].item() - avg_probs[0].item()
        
        # Apply keyword heuristics to refine score
        sentiment_score = self._apply_keyword_heuristics(text, sentiment_score)
        
        # Determine label based on adjusted score
        sentiment_label = self._get_label_from_score(sentiment_score)
        
        return {
            'sentiment_score': float(sentiment_score),
            'sentiment_label': sentiment_label,
            'confidence': float(confidence)
        }

    def _apply_keyword_heuristics(self, text: str, score: float) -> float:
        """
        Adjust sentiment score based on strong financial keywords.
        This helps when the model is uncertain or misses domain-specific context.
        """
        text_lower = text.lower()
        
        # Count occurrences
        pos_count = sum(1 for w in POSITIVE_KEYWORDS if w in text_lower)
        neg_count = sum(1 for w in NEGATIVE_KEYWORDS if w in text_lower)
        
        # Net keyword sentiment
        net_keywords = pos_count - neg_count
        
        # Adjustment factor (0.05 per keyword, max 0.3 adjustment)
        adjustment = max(min(net_keywords * 0.05, 0.3), -0.3)
        
        # If score is near zero (neutral), give keywords more weight
        if -0.2 < score < 0.2:
            if abs(net_keywords) >= 2:
                # Strong signal from keywords, weak signal from model
                # Boost the score significantly towards the keywords
                score += adjustment * 1.5
            else:
                score += adjustment
        else:
            # If model is already confident, just nudge it slightly
            score += adjustment * 0.5
            
        # Clamp score between -1 and 1
        return max(min(score, 1.0), -1.0)

    def _get_label_from_score(self, score: float) -> str:
        """Map score to label with stricter thresholds"""
        # Lower threshold slightly to capture more signals, 
        # but rely on keyword boosting for accuracy
        threshold = 0.15
        
        if score > threshold:
            return 'positive'
        elif score < -threshold:
            return 'negative'
        else:
            return 'neutral'
    
    def get_sentiment_stats(self, texts: List[str]) -> Dict[str, float]:
        """
        Get aggregate sentiment statistics for multiple texts
        """
        results = self.analyze_batch(texts)
        
        if not results:
            return {
                'avg_sentiment': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'avg_confidence': 0.0
            }
        
        sentiments = [r['sentiment_score'] for r in results]
        labels = [r['sentiment_label'] for r in results]
        confidences = [r['confidence'] for r in results]
        
        total = len(results)
        
        return {
            'avg_sentiment': np.mean(sentiments),
            'positive_ratio': labels.count('positive') / total,
            'negative_ratio': labels.count('negative') / total,
            'neutral_ratio': labels.count('neutral') / total,
            'avg_confidence': np.mean(confidences)
        }
