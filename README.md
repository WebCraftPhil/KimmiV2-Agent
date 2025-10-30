# KimmiV2-Agent

## Environment Setup
- Copy `config/openrouter.env.example` to `.env` at the repo root.
- Populate `OPENROUTER_API_KEY` with your OpenRouter token.
- Adjust `OPENROUTER_DEFAULT_MODEL` or `OPENROUTER_REQUEST_TIMEOUT` if desired.

## Quick Model Smoke Test
- Activate your Python environment and install dependencies from `requirements.txt`.
- Run `python scripts/test_openrouter.py "Draft a trend summary for luxury skincare"`.
- Override the system prompt if needed with `--system "You are ..."`.