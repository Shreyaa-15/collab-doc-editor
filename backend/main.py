import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import DefaultDict
from collections import defaultdict

from models import CreateDocument, DocumentResponse
from db import init_db, create_document, get_document, list_documents, update_document, save_operation, get_operations_since
from ot import apply_all, transform_all

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
        # doc_id -> list of (websocket, user_id, color)
        self.rooms: DefaultDict[str, list] = defaultdict(list)

    async def connect(self, doc_id: str, ws: WebSocket, user_id: str, color: str):
        await ws.accept()
        self.rooms[doc_id].append((ws, user_id, color))

    def disconnect(self, doc_id: str, ws: WebSocket):
        self.rooms[doc_id] = [(w, u, c) for w, u, c in self.rooms[doc_id] if w != ws]

    async def broadcast(self, doc_id: str, message: dict, exclude: WebSocket = None):
        for ws, user_id, color in self.rooms[doc_id]:
            if ws != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    def get_users(self, doc_id: str) -> list[dict]:
        return [{"user_id": u, "color": c} for _, u, c in self.rooms[doc_id]]

manager = ConnectionManager()

# --- REST endpoints ---

@app.post("/api/documents")
def create_doc(body: CreateDocument):
    doc = create_document(body.title, body.owner)
    return doc

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
    ops = get_operations_since(doc_id, since)
    return {"operations": ops}

# --- WebSocket endpoint ---

COLORS = ["#f38ba8", "#a6e3a1", "#89dceb", "#fab387", "#cba6f7", "#f9e2af"]

@app.websocket("/ws/{doc_id}/{user_id}")
async def websocket_endpoint(ws: WebSocket, doc_id: str, user_id: str):
    # Pick a color based on how many users are already in the room
    color = COLORS[len(manager.rooms[doc_id]) % len(COLORS)]

    await manager.connect(doc_id, ws, user_id, color)

    # Send current doc state to the newly connected user
    doc = get_document(doc_id)
    if doc:
        await ws.send_json({
            "type": "init",
            "content": doc["content"],
            "revision": doc["revision"],
            "users": manager.get_users(doc_id)
        })

    # Notify others that a new user joined
    await manager.broadcast(doc_id, {
        "type": "user_joined",
        "user_id": user_id,
        "color": color,
        "users": manager.get_users(doc_id)
    }, exclude=ws)

    try:
        while True:
            data = await ws.receive_json()

            # --- Handle text operation ---
            if data["type"] == "operation":
                doc = get_document(doc_id)
                if not doc:
                    continue

                incoming_ops  = data["ops"]
                client_rev    = data["revision"]
                server_rev    = doc["revision"]

                # Transform incoming ops against any ops we received since client's revision
                if client_rev < server_rev:
                    concurrent = get_operations_since(doc_id, client_rev)
                    for c in concurrent:
                        server_ops = json.loads(c["ops_json"])
                        incoming_ops = transform_all(incoming_ops, server_ops)

                # Apply to document
                new_content = apply_all(doc["content"], incoming_ops)
                new_revision = server_rev + 1
                update_document(doc_id, new_content, new_revision)
                save_operation(doc_id, user_id, new_revision, json.dumps(incoming_ops))

                # Broadcast to all other clients
                await manager.broadcast(doc_id, {
                    "type": "operation",
                    "ops": incoming_ops,
                    "revision": new_revision,
                    "user_id": user_id
                }, exclude=ws)

                # Acknowledge to sender
                await ws.send_json({
                    "type": "ack",
                    "revision": new_revision
                })

            # --- Handle cursor move ---
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