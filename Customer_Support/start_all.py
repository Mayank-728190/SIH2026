import subprocess
import sys
import time
import os
from pathlib import Path

# Always use the venv Python interpreter so all packages are available
BASE_DIR = Path(__file__).parent
VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"

# Fallback to sys.executable if venv not found (e.g. already inside venv)
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

def kill_process_tree(pid):
    if os.name == 'nt':
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        import signal
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            pass

def main():
    print(f"🚀 Starting all Continuum services...")
    print(f"   Python: {PYTHON}\n")
    
    processes = []
    
    try:
        # 1. Start Frontend
        print("→ Starting Frontend (Vite)...")
        frontend_process = subprocess.Popen(
            "npm run dev",
            cwd=str(BASE_DIR / "frontend"),
            shell=True
        )
        processes.append(frontend_process)

        # 2. Start Backend API
        print("→ Starting Backend API (FastAPI on :8000)...")
        backend_process = subprocess.Popen(
            [PYTHON, "-m", "app.main"],
            cwd=str(BASE_DIR)
        )
        processes.append(backend_process)

        # Give the backend 3 seconds to bind its port before the agent starts
        time.sleep(3)

        # 3. Start Voice Agent Worker
        print("→ Starting Voice Agent Worker...")
        agent_process = subprocess.Popen(
            [PYTHON, "-m", "app.agents.voice_agent", "start"],
            cwd=str(BASE_DIR)
        )
        processes.append(agent_process)

        print("\n" + "="*54)
        print("✅  ALL SERVICES RUNNING")
        print("   Frontend:    http://localhost:5173")
        print("   Backend API: http://localhost:8000")
        print("   Press Ctrl+C to stop all services.")
        print("="*54 + "\n")

        # Keep the main thread alive until user hits Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services gracefully...")
    finally:
        for p in processes:
            kill_process_tree(p.pid)
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()

