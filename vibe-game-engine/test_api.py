import subprocess
import time
import requests
import sys

def test():
    print("Starting server...")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "api.main:app", "--port", "8000"], cwd=r"e:\Projects\GAMEDEV\XClaw Agentic Godot Game Engine\vibe-game-engine")
    time.sleep(2)
    
    try:
        print("Sending POST /runs...")
        res = requests.post("http://127.0.0.1:8000/runs", json={"prompt": "Make an endless runner game"})
        print(f"POST result: {res.json()}")
        run_id = res.json()["run_id"]
        
        print("Waiting 2 seconds for worker to process queue...")
        time.sleep(2)
        
        print(f"Sending GET /runs/{run_id}...")
        res2 = requests.get(f"http://127.0.0.1:8000/runs/{run_id}")
        data = res2.json()
        print(f"GET result: {data}")
        assert data["status"] == "completed", "Status wasn't completed!"
        print("Success! End to end logic works.")
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test()