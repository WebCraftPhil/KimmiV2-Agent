# ⚙️ CURSOR Rules — Kimmi V2 Agent Workflow

## Mission Snapshot
- Build a locally hosted multi-agent system that plans and executes TikTok-native marketing content.
- Ensure every agent response is JSON-serializable so it can flow into the web UI and downstream automations.
- Keep messaging short, visual-first, and niche-specific for the active `niche` variable provided by the orchestrator.

## Global Prompt Requirements
- Always use structured outputs with labeled fields; avoid free-form paragraphs.
- Default tone: energetic, data-aware, and TikTok-native while staying actionable for marketing teams.
- Hooks and captions must be under 20 words unless another limit is explicitly supplied.
- Explicitly reference the active `niche` and any `trendSource`, `platform`, or `style` values passed in the payload.
- Maintain JSON compatibility at every step (wrap strings in quotes, avoid trailing commas, and escape special characters).
- Validate token counts before sending to models; truncate non-critical notes first.

## Chain Orchestration (openai.js)
1. `summarizeTrend()` → Input `{ "niche": string, "trendSource": string, "notes": string }`; Output `{ "summary": string }`.
   - Keep summaries to one sentence (< 30 words) and highlight one surprising or high-signal fact when available.
2. `generateIdeas()` → Input `{ "niche": string, "summary": string }`; Output exactly three `{ "title", "angle", "callToAction" }` objects.
   - Each idea must be immediately actionable, reference the trend insight, and state a visual anchor.
3. `writeHooks()` → Input `{ "ideas": [...], "style": "AIDA" | "PAS" }`; Output three hooks in `{ "ideaRef", "structure", "hook" }` format.
   - Hooks must follow the specified framework, stay < 20 words, and emphasize curiosity, emotion, or surprise.
4. `estimatePerformance()` → Input `{ "hooks": [...], "platform": string }`; Output `{ "scores": [ { "ideaRef", "score", "rationale" } x3 ] }`.
   - Score must be `High`, `Medium`, or `Low`; cite one qualitative and one quantitative factor in each rationale when possible.
- Persist each step’s JSON to `data/logs/` for UI observability.

## Trend Summarizer Rules
- Extract the core trend insight using the supplied `notes` and `trendSource` context.
- Point to audience benefit or urgency; avoid generic statements like “This trend is popular.”
- If no meaningful signal exists, state this clearly and request additional input.

## Idea Generator Rules
- Always return exactly three distinct ideas tailored to the `niche`.
- Titles should be crisp (< 7 words) and swipe-worthy.
- `angle` must explain the creative strategy plus production notes (e.g., POV, split-screen, testimonial).
- `callToAction` should specify an action the creator takes on-camera, not a vague marketing suggestion.

## Hook Writer Rules
- Respect the requested structure (`AIDA` or `PAS`) and label it in `structure`.
- Trigger curiosity, tension, or aspiration within the first 5 words.
- Avoid filler phrases (“You won’t believe,” “Check this out”) unless the hook context demands them.
- If constrained by visual requirements, mention them explicitly (e.g., “Split-screen: Coach vs. Client”).

## Performance Estimator Rules
- Anchor each rationale in trend fit, originality, niche relevance, and visual potential.
- Include at least one metric or proxy (e.g., “+32% watch-through on duet formats last week”).
- Flag blockers (missing CTA, unclear visual) even if score is `Medium` or `High`.

## Error Handling & Recovery
- On blank or invalid model output, retry once with clarified instructions noting the failure reason.
- After two consecutive failures, return `"No idea generated – retry later."` and log the diagnostics to `data/logs/`.
- Never emit malformed JSON; validate before propagating to the next step.

## Documentation & Change Management
- When prompt templates or chain order changes, update both `openai.js` and `AGENTS.md` with the new behaviour.
- Log significant modifications, failures, or experiments in `WORKLOG.md` (date, owner, outcome).
- For major updates, add a short summary to `PROJECTOVERVIEW.md` to keep stakeholders aligned.

## Testing & QA
- Add automated schema checks to ensure each agent response matches its contract.
- Run linting on prompt files or scripts before committing.
- During manual tests, capture sample inputs/outputs and store them under `data/logs/` for future regression checks.

