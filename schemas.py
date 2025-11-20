"""
Database Schemas for Smart Second Brain

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(True, description="Whether user is active")


class Folder(BaseModel):
    name: str = Field(..., description="Folder display name")
    key: str = Field(..., description="Unique key identifier, e.g., 'ideas', 'tasks'")
    color: str = Field("#64748b", description="Hex color used in UI")
    icon: str = Field("folder", description="Icon hint for UI")
    priority: int = Field(0, description="Higher = more important")


class Thought(BaseModel):
    title: Optional[str] = Field(None, description="Short title")
    content: Optional[str] = Field(None, description="Primary text content")
    modality: str = Field(..., description="text | image | link | voice")
    source_url: Optional[str] = Field(None, description="Original URL if any")
    image_data_url: Optional[str] = Field(None, description="Base64 data URL for images (small uploads)")
    tags: List[str] = Field(default_factory=list, description="Assigned tags")
    folder: Optional[str] = Field(None, description="Assigned folder key")
    meta: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
    pinned: bool = Field(False, description="User pinned to keep active")
    status: str = Field("active", description="active | snoozed | archived")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
