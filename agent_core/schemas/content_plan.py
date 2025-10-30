"""Example schema describing TikTok-ready content plans."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ContentIdea(BaseModel):
    title: str
    angle: str
    call_to_action: str
    performance_score: Literal["High", "Medium", "Low"] = "Medium"


class ContentPlan(BaseModel):
    niche: str
    trend_summary: str
    ideas: list[ContentIdea] = Field(default_factory=list)


