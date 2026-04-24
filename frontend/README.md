# Real-Time Collaborative Document Editor

A Google Docs-style collaborative editor where multiple users can edit the same document simultaneously with conflict resolution.

## Features
- Real-time collaboration via WebSockets
- Conflict resolution using Operational Transformation (OT)
- Rich text editing — bold, italic, headers, lists, code blocks
- Image embedding (base64, persisted to DB)
- Live cursor tracking — see where other users are
- Full persistence — documents saved to SQLite, survive page refresh
- Revision history logged for every operation

## Tech Stack
- **Frontend:** React, Vite, Quill.js
- **Backend:** FastAPI (Python), WebSockets
- **Conflict resolution:** Operational Transformation (OT) — implemented from scratch
- **Database:** SQLite

## How OT works
Every keystroke becomes an operation: `Insert(pos, char)` or `Delete(pos, len)`. When two users edit simultaneously, the server transforms concurrent operations against each other so both clients converge to the same document state — the same algorithm Google Docs uses.

## Run Locally

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — create a document, share the URL, open in another tab and type simultaneously.