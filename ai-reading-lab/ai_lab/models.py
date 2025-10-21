from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class Quote(BaseModel):
    text: str
    span: Optional[str] = None

class Summary(BaseModel):
    title: str
    authors: List[str] = Field(default_factory=list)
    venue: Optional[str] = None
    year: Optional[int] = None
    tl_dr: str = ""
    contributions: List[str] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    results: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    quotes: List[Quote] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    source_path: Optional[str] = None
