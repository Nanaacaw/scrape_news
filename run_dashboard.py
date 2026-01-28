"""
Quick launcher script for Streamlit dashboard
"""
import subprocess
import sys

if __name__ == '__main__':
    print("🚀 Launching CNBC Market Sentiment Dashboard...")
    subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'src/dashboard/app.py'])
