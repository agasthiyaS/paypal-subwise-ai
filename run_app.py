import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("=" * 70)
    print("   PayPal SubWise AI — Intelligent Cash-Flow & Subscription Guard")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    venv_python = os.path.join(backend_dir, "venv", "Scripts", "python.exe")

    if not os.path.exists(venv_python):
        venv_python = sys.executable

    # Ensure database is seeded with demo account
    print("\n[1/3] Ensuring demo business data & subscription intelligence are seeded...")
    seed_script = os.path.join(backend_dir, "seed.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = backend_dir
    subprocess.run([venv_python, seed_script], env=env, check=False)

    print("\n[2/3] Starting PayPal SubWise AI Backend Server...")
    print("      Server URL: http://127.0.0.1:8000")
    print("      Interactive Swagger Docs: http://127.0.0.1:8000/docs")
    print("      Unified Web Application: http://127.0.0.1:8000")

    # Start uvicorn
    print("\n[3/3] Launching web browser...")
    time.sleep(1.5)
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

    try:
        import uvicorn
        from app.main import app
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    except ImportError:
        subprocess.run([venv_python, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"], cwd=backend_dir, env=env)

if __name__ == "__main__":
    main()

