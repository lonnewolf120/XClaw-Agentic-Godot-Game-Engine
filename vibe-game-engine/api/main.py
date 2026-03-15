from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.runs import router as runs_router
from workers.processor import WorkerProcessor
from store.run_store import RunStore
from workers.queue import queue_instance

worker: WorkerProcessor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker
    store = RunStore()
    worker = WorkerProcessor(store, queue_instance)
    worker.start()
    yield
    worker.stop()

app = FastAPI(title="Vibe Game Engine Backend", version="v0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)

@app.get("/health")
def health_check():
    return {"status": "ok", "mode": "Phase 0 Skeleton"}

def start_server():
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    start_server()
