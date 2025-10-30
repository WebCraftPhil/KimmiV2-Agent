# KimmiV2-Agent

## Repository Setup
- Initialize a new Git repository if one is not already present: `git init`.
- Create the remote repository `kimmi-v2-openrouter` on GitHub via the UI or `gh repo create`.
- Link the remote: `git remote add origin git@github.com:<your-handle>/kimmi-v2-openrouter.git`.
- Push the current branch after committing: `git push -u origin main`.

## Environment Setup
- Copy `config/openrouter.env.example` to `.env` at the repo root.
- Populate `OPENROUTER_API_KEY` with your OpenRouter token.
- Adjust `OPENROUTER_DEFAULT_MODEL` or `OPENROUTER_REQUEST_TIMEOUT` if desired.

## Quick Model Smoke Test
- Activate your Python environment and install dependencies from `requirements.txt`.
- Run `python scripts/test_openrouter.py "Draft a trend summary for luxury skincare"`.
- Override the system prompt if needed with `--system "You are ..."`.

## Frontend (Next.js)
- Install dependencies: `cd web && npm install`.
- Run the dev server: `npm run dev` (defaults to `http://localhost:3000`).
- Ensure the FastAPI backend is running on `http://localhost:8000` or set `AGENT_BASE_URL` before starting the dev server.