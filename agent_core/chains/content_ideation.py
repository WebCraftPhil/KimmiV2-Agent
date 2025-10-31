"""Four-step content ideation chain for Kimmi V2."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Tuple

from agent_core.models import AgentMessage, ModelReply

FallbackString = "No idea generated – retry later."


class ContentChainError(RuntimeError):
    """Raised when the content chain cannot produce a valid result."""


@dataclass
class ContentChainInput:
    niche: str
    trend_source: str
    notes: str
    style: Literal["AIDA", "PAS"] = "AIDA"
    platform: str = "TikTok"


@dataclass
class ContentChainArtifacts:
    result: Dict[str, Any]
    step_outputs: Dict[str, Any]
    raw_replies: Dict[str, Dict[str, Any]]


class ContentIdeationChain:
    """Executes the summarize → ideas → hooks → performance pipeline."""

    def __init__(self, lm_client, max_retries: int = 2) -> None:
        self._lm_client = lm_client
        self._max_retries = max_retries

    async def run(self, payload: ContentChainInput) -> ContentChainArtifacts:
        """Execute each step of the chain and capture intermediate artifacts."""
        # Step 1: Summarize the incoming trend signal into a single sentence.
        summary, summary_reply = await self._summarize_trend(payload)
        # Step 2: Expand the summary into three production-ready content ideas.
        ideas, ideas_reply = await self._generate_ideas(payload, summary)
        # Step 3: Translate each idea into a short-form hook using the requested structure.
        hooks, hooks_reply = await self._write_hooks(payload, ideas)
        # Step 4: Score hooks for performance confidence on the specified platform.
        scores, scores_reply = await self._estimate_performance(payload, hooks)

        result = {
            "niche": payload.niche,
            "trendSource": payload.trend_source,
            "style": payload.style,
            "platform": payload.platform,
            "summary": summary,
            "ideas": ideas,
            "hooks": hooks,
            "scores": scores,
        }

        step_outputs = {
            "summarizeTrend": {"summary": summary},
            "generateIdeas": {"ideas": ideas},
            "writeHooks": {"hooks": hooks},
            "estimatePerformance": {"scores": scores},
        }

        raw_replies = {
            "summarizeTrend": summary_reply.raw,
            "generateIdeas": ideas_reply.raw,
            "writeHooks": hooks_reply.raw,
            "estimatePerformance": scores_reply.raw,
        }

        return ContentChainArtifacts(result=result, step_outputs=step_outputs, raw_replies=raw_replies)

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    async def _summarize_trend(self, payload: ContentChainInput) -> Tuple[str, ModelReply]:
        system_prompt = (
            "You are summarizeTrend. Keep outputs < 30 words, cite one surprising or high-signal fact when available. "
            "Respond with JSON only, shaped as {\"summary\": string}."
        )

        user_payload = {
            "niche": payload.niche,
            "trendSource": payload.trend_source,
            "notes": payload.notes,
        }

        data, reply = await self._call_json_model(
            messages=[
                AgentMessage(role="system", content=system_prompt),
                AgentMessage(
                    role="user",
                    content=json.dumps(user_payload),
                ),
            ],
            required_keys=["summary"],
        )
        return data["summary"], reply

    async def _generate_ideas(self, payload: ContentChainInput, summary: str) -> Tuple[List[Dict[str, Any]], ModelReply]:
        system_prompt = (
            "You are generateIdeas. Produce exactly three ideas tailored to the niche. "
            "Each idea must include title (<7 words), angle with production notes, and callToAction describing on-camera action. "
            "Reference the trend insight. Respond with JSON {\"ideas\": [ ... ]}."
        )

        user_payload = {
            "niche": payload.niche,
            "summary": summary,
        }

        data, reply = await self._call_json_model(
            messages=[
                AgentMessage(role="system", content=system_prompt),
                AgentMessage(role="user", content=json.dumps(user_payload)),
            ],
            required_keys=["ideas"],
        )

        ideas = data["ideas"]
        if len(ideas) != 3:
            raise ContentChainError("generateIdeas must return exactly three ideas")
        return ideas, reply

    async def _write_hooks(
        self,
        payload: ContentChainInput,
        ideas: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], ModelReply]:
        system_prompt = (
            "You are writeHooks. Convert each idea into a hook under 20 words using the specified structure. "
            "Emphasize curiosity, emotion, or surprise. Respond with JSON {\"hooks\": [ ... ]}."
        )

        user_payload = {
            "ideas": ideas,
            "style": payload.style,
        }

        data, reply = await self._call_json_model(
            messages=[
                AgentMessage(role="system", content=system_prompt),
                AgentMessage(role="user", content=json.dumps(user_payload)),
            ],
            required_keys=["hooks"],
        )

        hooks = data["hooks"]
        if len(hooks) != 3:
            raise ContentChainError("writeHooks must return three hooks")
        return hooks, reply

    async def _estimate_performance(
        self,
        payload: ContentChainInput,
        hooks: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], ModelReply]:
        system_prompt = (
            "You are estimatePerformance. Score each hook as High, Medium, or Low for the given platform. "
            "Cite one qualitative and one quantitative factor when possible. Respond with JSON {\"scores\": [ ... ]}."
        )

        user_payload = {
            "hooks": hooks,
            "platform": payload.platform,
        }

        data, reply = await self._call_json_model(
            messages=[
                AgentMessage(role="system", content=system_prompt),
                AgentMessage(role="user", content=json.dumps(user_payload)),
            ],
            required_keys=["scores"],
        )

        scores = data["scores"]
        if len(scores) != 3:
            raise ContentChainError("estimatePerformance must return three scores")
        return scores, reply

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _call_json_model(
        self,
        messages: List[AgentMessage],
        required_keys: List[str],
    ) -> Tuple[Dict[str, Any], ModelReply]:
        """Send a JSON-only request to the LLM with retry + validation logic."""
        # Copy the original messages so we can mutate the list during retries.
        msgs = list(messages)
        for attempt in range(self._max_retries):
            reply = await self._lm_client.generate(msgs)
            content = reply.message.content.strip()
            try:
                data = self._parse_json_content(content)
            except ValueError as exc:
                if attempt + 1 >= self._max_retries:
                    raise ContentChainError(str(exc)) from exc
                # Append an instruction reminding the model to stay in JSON.
                msgs = msgs + [
                    AgentMessage(
                        role="system",
                        content="The previous output was invalid JSON. Respond with valid JSON only, no prose.",
                    )
                ]
                continue

            missing = [key for key in required_keys if key not in data]
            if missing:
                if attempt + 1 >= self._max_retries:
                    raise ContentChainError(f"Missing keys in model output: {missing}")
                # Ask the model to retry with the missing fields included.
                msgs = msgs + [
                    AgentMessage(
                        role="system",
                        content=f"The previous output missing keys {missing}. Return complete JSON payload.",
                    )
                ]
                continue

            return data, reply

        raise ContentChainError("Model failed to return valid JSON")

    @staticmethod
    def _parse_json_content(content: str) -> Dict[str, Any]:
        """Parse JSON responses while tolerating optional markdown code fences."""
        if not content:
            raise ValueError("Model returned empty content")

        stripped = content.strip()
        if stripped.startswith("```"):
            # Remove code fences like ```json ... ```
            parts = stripped.split("```")
            if len(parts) >= 3:
                # parts[1] may look like "json"; parts[2] holds the actual payload.
                stripped = parts[2].strip() if parts[1].strip().startswith("json") else parts[1].strip()

        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON response: {exc}") from exc


__all__ = [
    "ContentChainArtifacts",
    "ContentChainError",
    "ContentChainInput",
    "ContentIdeationChain",
    "FallbackString",
]


