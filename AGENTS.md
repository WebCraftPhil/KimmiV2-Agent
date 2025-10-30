# Kimmi V2 Agents Playbook

## Mission & Operating Context
- Build a locally hosted multi-agent workflow that plans and executes short-form content strategies for marketing teams.
- All agent interactions must stay compatible with JSON serialization so responses can be consumed by the web UI and downstream automations.
- Prompts must stay short, scannable, and TikTok-native while preserving niche-specific detail.

## Global Prompt Rules
- Use structured outputs with labeled fields; avoid free-form prose.
- Always tailor messaging to the active `niche` variable supplied by the orchestrator.
- Prefer AIDA or PAS structures when writing hooks; keep hooks under 20 words.
- Provide exactly three ideas or hooks when requested; ideas must be actionable and niche-aligned.
- Apply performance scoring as `High`, `Medium`, or `Low` based on trend fit, originality, niche alignment, and visual potential.
- On blank or invalid generations, retry once before returning the fallback string `"No idea generated – retry later."`

## Agent Chain Overview
1. **Trend Summarizer** (`summarizeTrend`)
   - Purpose: Digest the latest trend signal or brief into a single sentence summary.
   - Input: `{ "niche": string, "trendSource": string, "notes": string }`
   - Output: `{ "summary": string }`
   - Prompt Notes: Keep sentence length < 30 words, include one surprising or high-signal fact when available.

2. **Idea Generator** (`generateIdeas`)
   - Purpose: Produce three creative, niche-aligned content ideas from the trend summary.
   - Input: `{ "niche": string, "summary": string }`
   - Output: `{ "ideas": [ { "title": string, "angle": string, "callToAction": string } x3 ] }`
   - Prompt Notes: Ensure every idea is immediately actionable, references the trend insight, and specifies a visual anchor.

3. **Hook Writer** (`writeHooks`)
   - Purpose: Convert each idea into a sub-20-word hook following AIDA or PAS.
   - Input: `{ "ideas": [...], "style": "AIDA" | "PAS" }`
   - Output: `{ "hooks": [ { "ideaRef": string, "structure": string, "hook": string } x3 ] }`
   - Prompt Notes: Emphasize curiosity, emotional resonance, or surprise; explicitly note which structure is applied.

4. **Performance Estimator** (`estimatePerformance`)
   - Purpose: Predict how each hook will perform across specified metrics.
   - Input: `{ "hooks": [...], "platform": string }`
   - Output: `{ "scores": [ { "ideaRef": string, "score": "High" | "Medium" | "Low", "rationale": string } x3 ] }`
   - Prompt Notes: Cite one qualitative and one quantitative factor in each rationale when possible.

## Orchestration Guidelines
- The orchestrator executes the chain sequentially: summarize → generate ideas → write hooks → estimate performance.
- Each step receives the prior step’s output; persist intermediate JSON for observability in the UI.
- Validate token counts per call to stay within model limits; truncate non-critical fields if required.
- Log significant deviations or retries to `data/logs/` for post-run analysis.

## Error Handling & Recovery
- If any step fails validation, retry with a clarified instruction noting the failure reason.
- After two consecutive failures, abort the chain and return the fallback string with diagnostic metadata.
- Record failures and resolutions in `WORKLOG.md` under the “Open Issues” section.

## Change Management
- When prompt templates or chaining order changes, update the corresponding logic in `openai.js` and reflect the new behaviour in this document under the relevant sections.
- Document each significant modification, experiment, or unblock in `WORKLOG.md`, including date, owner, and outcome.
- For larger updates, add a short summary to `PROJECTOVERVIEW.md` to keep stakeholders aligned on direction.

## Future Enhancements
- Introduce role-specific memory modules (trend history, creative swipe file) and describe them here once implemented.
- Expand the agent roster as new MCP tools come online and detail their contracts using the format above.
- Add automated tests that validate JSON schema compliance for every agent response.

