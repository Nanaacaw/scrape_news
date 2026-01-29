import subprocess
import sys
import os

if __name__ == '__main__':
    print("🚀 Launching CNBC Market Sentiment Dashboard...")
    print("💡 Tip: Press Ctrl+C to stop the server")
    print("")
    
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 
        'src/dashboard/app.py',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false',
        '--server.fileWatcherType', 'none'
    ])
