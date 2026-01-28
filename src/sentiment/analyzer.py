"""
Sentiment Analysis Engine using IndoBERT
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Dict, Tuple
import numpy as np

from src.utils.config import SENTIMENT_MODEL, SENTIMENT_BATCH_SIZE, SENTIMENT_MAX_LENGTH
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SentimentAnalyzer:
    """
    Sentiment analyzer using IndoBERT pre-trained model
    
    Sentiment labels:
    - positive: score > 0.3
    - negative: score < -0.3
    - neutral: -0.3 <= score <= 0.3
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
            # For IndoBERT, we'll use it as a feature extractor
            # and apply simple sentiment classification
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Try to load a sentiment model, fallback to base model
            try:
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    "w11wo/indonesian-roberta-base-sentiment-classifier"
                )
                self.use_sentiment_head = True
                logger.info("Using dedicated sentiment classification model")
            except:
                # If sentiment model not available, we'll use IndoBERT with simple heuristics
                logger.warning("Sentiment classifier not found, using IndoBERT base model")
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=3  # positive, neutral, negative
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
        Analyze sentiment of a single text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment_score, sentiment_label, and confidence
        """
        results = self.analyze_batch([text])
        return results[0] if results else None
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Analyze sentiment of multiple texts in batch
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of dictionaries with sentiment results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(texts), SENTIMENT_BATCH_SIZE):
            batch_texts = texts[i:i + SENTIMENT_BATCH_SIZE]
            batch_results = self._process_batch(batch_texts)
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """Process a single batch of texts"""
        try:
            # Tokenize
            inputs = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=SENTIMENT_MAX_LENGTH,
                return_tensors='pt'
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Process predictions
            probabilities = torch.softmax(logits, dim=-1)
            predictions = torch.argmax(probabilities, dim=-1)
            confidences = torch.max(probabilities, dim=-1).values
            
            # Convert to numpy
            predictions = predictions.cpu().numpy()
            confidences = confidences.cpu().numpy()
            probabilities = probabilities.cpu().numpy()
            
            # Convert to sentiment scores and labels
            results = []
            for pred, conf, probs in zip(predictions, confidences, probabilities):
                sentiment_score, sentiment_label = self._convert_prediction(pred, probs)
                
                results.append({
                    'sentiment_score': float(sentiment_score),
                    'sentiment_label': sentiment_label,
                    'confidence': float(conf)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process batch: {e}")
            # Return neutral sentiment as fallback
            return [
                {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0
                }
                for _ in texts
            ]
    
    def _convert_prediction(self, prediction: int, probabilities: np.ndarray) -> Tuple[float, str]:
        """
        Convert model prediction to sentiment score and label
        
        Args:
            prediction: Predicted class (0=negative, 1=neutral, 2=positive)
            probabilities: Class probabilities
            
        Returns:
            (sentiment_score, sentiment_label)
            sentiment_score: -1 (very negative) to 1 (very positive)
        """
        # Map prediction to label
        label_map = {
            0: 'negative',
            1: 'neutral',
            2: 'positive'
        }
        
        sentiment_label = label_map.get(prediction, 'neutral')
        
        # Calculate sentiment score (-1 to 1)
        # Score = P(positive) - P(negative)
        if len(probabilities) >= 3:
            sentiment_score = probabilities[2] - probabilities[0]
        else:
            # Fallback for binary classification
            sentiment_score = 0.0 if prediction == 1 else (1.0 if prediction == 2 else -1.0)
        
        return sentiment_score, sentiment_label
    
    def get_sentiment_stats(self, texts: List[str]) -> Dict[str, float]:
        """
        Get aggregate sentiment statistics for multiple texts
        
        Returns:
            Dictionary with average sentiment and distribution
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
