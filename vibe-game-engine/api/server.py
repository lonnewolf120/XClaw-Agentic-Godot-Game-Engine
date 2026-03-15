from __future__ import annotations

import asyncio
import json
import logging
import uuid
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure tools are in path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from tools.godot_ast import build_starter_platformer

# We import the game creation engine and LLM manager
# from orchestration.game_creation import GameCreationEngine
# For the fake bridge implementation, we will mock the engine state yields 
# with cost-saving router logic inline.

app = FastAPI(title="Vibe Engine API", version="0.1.0")

# Allow CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

class PromptRequest(BaseModel):
    prompt: str

# Cost Saving Logic: Fast heuristic intent router
def fast_intent_router(prompt: str) -> dict:
    """
    Evaluates the prompt without calling a heavy LLM pipeline if it matches strictly 
    against known minimal templates. This saves vertex AI credits by skipping the planner 
    for simple boilerplate commands.
    """
    lower_px = prompt.lower()
    if "racing" in lower_px or "buggy" in lower_px:
        return {"template": "Top-Down Racing", "complexity": "low", "estimated_cost": 0.00}
    if "fps" in lower_px or "first person" in lower_px:
        return {"template": "FPS Controller", "complexity": "low", "estimated_cost": 0.00}
    if "platformer" in lower_px:
        return {"template": "3D Platformer", "complexity": "low", "estimated_cost": 0.00}
    
    # If no strict match, it flags as 'high' complexity necessitating the VertexAI Agents
    return {"template": "Starter-Kit-Basic-Scene", "complexity": "high", "estimated_cost": 0.02}


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "FastAPI Backend", "errors": []}

@app.post("/api/v1/generate")
async def start_generation(req: PromptRequest):
    """
    HTTP endpoint to trigger the generator. 
    In the real app, this would queue a job. Here it returns an immediate run ID.
    """
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    analysis = fast_intent_router(req.prompt)
    
    return {
        "status": "queued",
        "run_id": run_id,
        "analysis": analysis,
        "message": f"Generation starting. Complexity: {analysis['complexity']}"
    }


@app.websocket("/api/v1/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    await manager.connect(websocket)
    try:
        # Simulate LangGraph / Orchestration emitting step-by-step signals
        # Steps: intake -> bootstrap scene -> codegen -> validate -> ready
        
        await asyncio.sleep(1.0)
        await manager.send_personal_message(json.dumps({"type": "log", "data": "[Intake] Parsing prompt intent..."}), websocket)
        await manager.send_personal_message(json.dumps({"type": "step", "step": "Parse Guidelines", "status": "done"}), websocket)
        
        await asyncio.sleep(1.5)
        await manager.send_personal_message(json.dumps({"type": "log", "data": f"[Scene] Bootstrapping template for run {run_id}"}), websocket)
        
        # AST Generation (Cost Saving! Fast and Deterministic)
        tscn_content = build_starter_platformer()
        mock_scene_event = {
            "path": "res://scenes/main.tscn",
            "added": len(tscn_content.splitlines()),
            "deleted": 0,
            "content": tscn_content
        }
        await manager.send_personal_message(json.dumps({"type": "diff", "data": mock_scene_event}), websocket)
        await manager.send_personal_message(json.dumps({"type": "log", "data": "[Scene] AST Scene Builder completed successfully ($0.00 cost)."}), websocket)
        await manager.send_personal_message(json.dumps({"type": "step", "step": "Bootstrap Scene", "status": "done"}), websocket)
        
        await asyncio.sleep(2.0)
        # Using LLM Generation step (Using Vertex AI behind the scenes for actual run)
        await manager.send_personal_message(json.dumps({"type": "log", "data": "[CodeGen] Streamline coding agent patching scripts..."}), websocket)
        
        # Stream a fake diff
        mock_diff = {
            "path": "res://scripts/player.gd",
            "added": 12,
            "deleted": 2,
            "content": "extends CharacterBody3D\n\nconst SPEED = 5.0\n"
        }
        await manager.send_personal_message(json.dumps({"type": "diff", "data": mock_diff}), websocket)
        await manager.send_personal_message(json.dumps({"type": "step", "step": "Generate GDScript", "status": "done"}), websocket)
        
        await asyncio.sleep(1.5)
        await manager.send_personal_message(json.dumps({"type": "log", "data": "[Validation] Headless verifier executing pass..."}), websocket)
        await manager.send_personal_message(json.dumps({"type": "step", "step": "Headless Verification", "status": "done"}), websocket)
        
        await asyncio.sleep(0.5)
        await manager.send_personal_message(json.dumps({"type": "success", "run_id": run_id}), websocket)

        # Keep connection open for ping-pongs
        while True:
            data = await websocket.receive_text()
            # Handle incoming client messages (e.g. stop run, tweak scene)
            pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {run_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)