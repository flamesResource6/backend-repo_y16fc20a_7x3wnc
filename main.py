import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Thought, Folder

app = FastAPI(title="Smart Second Brain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class ThoughtCreate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    modality: str
    source_url: Optional[str] = None
    image_data_url: Optional[str] = None
    tags: Optional[List[str]] = None


def smart_route_folder(text: str | None, tags: List[str] | None) -> str:
    """Very simple heuristic router that mimics the future AI classifier.
    Maps incoming content to a folder key.
    """
    text_l = (text or "").lower()
    tagset = set([t.lower() for t in (tags or [])])

    # Priority rules
    if any(t in text_l for t in ["todo", "task", "next", "due", "deadline"]) or "task" in tagset:
        return "tasks"
    if any(t in text_l for t in ["idea", "concept", "brainstorm", "inspiration"]) or "idea" in tagset:
        return "ideas"
    if any(t in text_l for t in ["meeting", "call", "note", "summary"]) or "notes" in tagset:
        return "notes"
    if any(t in text_l for t in ["article", "read", "bookmark", "link"]) or "read" in tagset:
        return "reads"
    return "inbox"


@app.get("/")
def root():
    return {"message": "Smart Second Brain backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()[:10]
        else:
            response["database"] = "❌ Not Configured"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response


@app.get("/api/folders")
def get_folders():
    """Default system folders for the second brain."""
    return [
        {"key": "inbox", "name": "Inbox", "color": "#94a3b8", "icon": "inbox", "priority": 0},
        {"key": "ideas", "name": "Ideas", "color": "#22c55e", "icon": "sparkles", "priority": 3},
        {"key": "tasks", "name": "Tasks", "color": "#3b82f6", "icon": "check-circle", "priority": 4},
        {"key": "notes", "name": "Notes", "color": "#f59e0b", "icon": "notepad", "priority": 2},
        {"key": "reads", "name": "Reads", "color": "#ec4899", "icon": "book-open", "priority": 1},
    ]


@app.post("/api/ingest")
def ingest_thought(payload: ThoughtCreate):
    if payload.modality not in ["text", "image", "link", "voice"]:
        raise HTTPException(status_code=400, detail="Unsupported modality")

    folder = smart_route_folder(payload.content, payload.tags)
    doc = Thought(
        title=payload.title,
        content=payload.content,
        modality=payload.modality,
        source_url=payload.source_url,
        image_data_url=payload.image_data_url,
        tags=payload.tags or [],
        folder=folder,
        meta={"routed_by": "heuristic-v0"},
    )

    try:
        inserted_id = create_document("thought", doc)
        return {"ok": True, "id": inserted_id, "folder": folder}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/thoughts")
def list_thoughts(folder: Optional[str] = None, limit: int = 50):
    try:
        flt = {"folder": folder} if folder else {}
        docs = get_documents("thought", flt, limit)
        # Convert ObjectId to string
        for d in docs:
            if d.get("_id"):
                d["id"] = str(d.pop("_id"))
        return {"ok": True, "items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
