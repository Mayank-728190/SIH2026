import subprocess
import sys
import time
import signal
import os
from dotenv import load_dotenv

# Load environment variables from .env file so subprocesses inherit them
load_dotenv()

processes = []

def signal_handler(sig, frame):
    print("\nShutting down services...")
    for p in processes:
        p.terminate()
    sys.exit(0)

if __name__ == "__main__":
    print("Starting eKYC Backend Services...")
    
    # Listen for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    env = os.environ.copy()
    
    # Start FastAPI
    print("Starting FastAPI Server on port 8000...")
    fastapi_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        env=env
    )
    processes.append(fastapi_process)
    
    # Wait a bit for FastAPI to initialize
    time.sleep(2)
    
    # Start LiveKit Voice Agent
    print("Starting LiveKit Voice Agent Worker...")
    agent_process = subprocess.Popen(
        [sys.executable, "-m", "app.agent.voice_agent", "start"],
        env=env
    )
    processes.append(agent_process)
    
    print("\nAll services started! Access the frontend at: http://localhost:8000")
    print("Press Ctrl+C to stop all services.\n")
    
    # Keep the main thread alive
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)
