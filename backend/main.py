import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

from models import CreateDocument
from db import (init_db, create_document, get_document, list_documents,
                update_document, save_operation, get_operations_since)

app = FastAPI(title="Collab Doc Editor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# --- Connection manager ---

class ConnectionManager:
    def __init__(self):
        self.rooms = defaultdict(list)

    async def connect(self, doc_id, ws, user_id, color):
        await ws.accept()
        self.rooms[doc_id].append((ws, user_id, color))

    def disconnect(self, doc_id, ws):
        self.rooms[doc_id] = [(w, u, c) for w, u, c in self.rooms[doc_id] if w != ws]

    async def broadcast(self, doc_id, message, exclude=None):
        for ws, user_id, color in self.rooms[doc_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    def get_users(self, doc_id):
        return [{"user_id": u, "color": c} for _, u, c in self.rooms[doc_id]]

manager = ConnectionManager()
COLORS = ["#f38ba8", "#a6e3a1", "#89dceb", "#fab387", "#cba6f7", "#f9e2af"]

# --- REST endpoints ---

@app.post("/api/documents")
def create_doc(body: CreateDocument):
    return create_document(body.title, body.owner)

@app.get("/api/documents")
def list_docs():
    return list_documents()

@app.get("/api/documents/{doc_id}")
def get_doc(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/documents/{doc_id}/history")
def get_history(doc_id: str, since: int = 0):
    return {"operations": get_operations_since(doc_id, since)}

# --- WebSocket endpoint ---

@app.websocket("/ws/{doc_id}/{user_id}")
async def websocket_endpoint(ws: WebSocket, doc_id: str, user_id: str):
    color = COLORS[len(manager.rooms[doc_id]) % len(COLORS)]
    await manager.connect(doc_id, ws, user_id, color)

    doc = get_document(doc_id)
    if doc:
        # Parse stored delta or fall back to plain text
        try:
            stored = json.loads(doc["content"]) if doc["content"] else {"ops": []}
        except Exception:
            stored = {"ops": [{"insert": doc["content"] or ""}]}

        await ws.send_json({
            "type": "init",
            "delta": stored,
            "revision": doc["revision"],
            "users": manager.get_users(doc_id)
        })

    await manager.broadcast(doc_id, {
        "type": "user_joined",
        "user_id": user_id,
        "color": color,
        "users": manager.get_users(doc_id)
    }, exclude=ws)

    try:
        while True:
            data = await ws.receive_json()

            if data["type"] == "operation":
                doc = get_document(doc_id)
                if not doc:
                    continue

                delta = data.get("delta", {})
                delta_json = json.dumps(delta)
                new_revision = doc["revision"] + 1

                update_document(doc_id, delta_json, new_revision)
                save_operation(doc_id, user_id, new_revision, delta_json)

                await manager.broadcast(doc_id, {
                    "type": "operation",
                    "delta": delta,
                    "revision": new_revision,
                    "user_id": user_id
                }, exclude=ws)

                await ws.send_json({
                    "type": "ack",
                    "revision": new_revision
                })

            elif data["type"] == "cursor":
                await manager.broadcast(doc_id, {
                    "type": "cursor",
                    "user_id": user_id,
                    "color": color,
                    "index": data["index"]
                }, exclude=ws)

    except WebSocketDisconnect:
        manager.disconnect(doc_id, ws)
        await manager.broadcast(doc_id, {
            "type": "user_left",
            "user_id": user_id,
            "users": manager.get_users(doc_id)
        })