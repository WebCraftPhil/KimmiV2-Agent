import Head from 'next/head';
import { FormEvent, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { z } from 'zod';

const JsonViewer = dynamic(
  () =>
    import('@textea/json-viewer').then((mod) => {
      return mod.JsonViewer;
    }),
  { ssr: false }
);

type AgentResponse = {
  message: {
    role: string;
    content: string;
    name?: string | null;
  };
  tool_results: Array<Record<string, unknown>>;
  raw: Record<string, unknown>;
};

const TrendChainSchema = z.object({
  niche: z.string(),
  trendSource: z.string(),
  style: z.string(),
  platform: z.string(),
  summary: z.string(),
  ideas: z
    .array(
      z.object({
        title: z.string(),
        angle: z.string(),
        callToAction: z.string(),
      })
    )
    .length(3),
  hooks: z
    .array(
      z.object({
        ideaRef: z.string(),
        structure: z.string(),
        hook: z.string(),
      })
    )
    .length(3),
  scores: z
    .array(
      z.object({
        ideaRef: z.string(),
        score: z.string(),
        rationale: z.string(),
      })
    )
    .length(3),
});

type TrendChainResult = z.infer<typeof TrendChainSchema>;

export default function Home() {
  const [niche, setNiche] = useState('Luxury skincare founders');
  const [trendSource, setTrendSource] = useState('TikTok Creative Center – Week 44 sound spikes');
  const [notes, setNotes] = useState(
    'Emerging trend: slow-motion texture shots with ASMR voiceovers. Audience obsessed with dermatologist-led routines.'
  );
  const [style, setStyle] = useState<'AIDA' | 'PAS'>('AIDA');
  const [platform, setPlatform] = useState('TikTok');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const trimmedNiche = niche.trim();
      const trimmedNotes = notes.trim();
      if (!trimmedNiche || !trimmedNotes) {
        throw new Error('Niche and notes are required.');
      }

      const res = await fetch('/api/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          niche: trimmedNiche,
          trendSource: trendSource.trim() || 'unspecified',
          notes: trimmedNotes,
          style,
          platform: platform.trim() || 'TikTok',
        })
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error((detail && detail.detail) || res.statusText);
      }

      const data: AgentResponse = await res.json();
      setResponse(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  const parsedResult = useMemo<TrendChainResult | null>(() => {
    if (!response) return null;
    try {
      const raw = JSON.parse(response.message.content);
      return TrendChainSchema.parse(raw);
    } catch (err) {
      console.warn('Failed to parse chain output', err);
      return null;
    }
  }, [response]);

  return (
    <>
      <Head>
        <title>Kimmi V2 Console</title>
        <meta name="description" content="Interact with the Kimmi V2 agent locally." />
      </Head>
      <main className="layout">
        <section className="panel prompt-panel">
          <h1>Kimmi V2 Agent</h1>
          <p className="subtitle">Local multi-agent marketing playground</p>

          <form onSubmit={submit} className="prompt-form">
            <label htmlFor="niche">Niche</label>
            <input
              id="niche"
              value={niche}
              onChange={(event) => setNiche(event.target.value)}
              placeholder="e.g., Luxury skincare founders"
            />

            <label htmlFor="trend-source">Trend Source</label>
            <input
              id="trend-source"
              value={trendSource}
              onChange={(event) => setTrendSource(event.target.value)}
              placeholder="Where did this signal come from?"
            />

            <label htmlFor="notes">Trend Notes</label>
            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={6}
              placeholder="Key observations, constraints, audience insights..."
            />

            <div className="row">
              <div className="field-group">
                <label htmlFor="style">Hook Style</label>
                <select
                  id="style"
                  value={style}
                  onChange={(event) => setStyle(event.target.value as 'AIDA' | 'PAS')}
                >
                  <option value="AIDA">AIDA</option>
                  <option value="PAS">PAS</option>
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="platform">Platform</label>
                <input
                  id="platform"
                  value={platform}
                  onChange={(event) => setPlatform(event.target.value)}
                  placeholder="TikTok"
                />
              </div>
            </div>

            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Running chain…' : 'Run 4-Step Chain'}
            </button>
          </form>

          {error && <p className="error">{error}</p>}
        </section>

        <section className="panel response-panel">
          <h2>Assistant Response</h2>
          {response ? (
            <div className="response-content">
              {parsedResult ? (
                <>
                  <article className="assistant-message">
                    <h3>Trend Summary</h3>
                    <p>{parsedResult.summary}</p>
                  </article>

                  <article>
                    <h3>Ideas</h3>
                    <ul className="idea-list">
                      {parsedResult.ideas.map((idea, index) => (
                        <li key={idea.title + index}>
                          <strong>{idea.title}</strong>
                          <span>{idea.angle}</span>
                          <em>{idea.callToAction}</em>
                        </li>
                      ))}
                    </ul>
                  </article>

                  <article>
                    <h3>Hooks ({parsedResult.style})</h3>
                    <ul className="hook-list">
                      {parsedResult.hooks.map((hook) => (
                        <li key={hook.ideaRef}>
                          <span className="badge">{hook.structure}</span>
                          <span>{hook.hook}</span>
                        </li>
                      ))}
                    </ul>
                  </article>

                  <article>
                    <h3>Performance Scores – {parsedResult.platform}</h3>
                    <ul className="score-list">
                      {parsedResult.scores.map((score) => (
                        <li key={score.ideaRef}>
                          <div className="score-header">
                            <strong>{score.ideaRef}</strong>
                            <span className={`score score-${score.score.toLowerCase()}`}>
                              {score.score}
                            </span>
                          </div>
                          <small>{score.rationale}</small>
                        </li>
                      ))}
                    </ul>
                  </article>

                  <article>
                    <h3>Structured Output</h3>
                    <JsonViewer
                      value={parsedResult}
                      defaultInspectDepth={1}
                      enableClipboard={false}
                      rootName={false}
                      theme="dark"
                    />
                  </article>
                </>
              ) : (
                <article className="assistant-message">
                  <h3>Raw Message</h3>
                  <pre>{response.message.content}</pre>
                </article>
              )}

              <article>
                <h3>Tool Results</h3>
                {response.tool_results.length === 0 ? (
                  <p className="muted">No tools invoked.</p>
                ) : (
                  <JsonViewer
                    value={response.tool_results}
                    defaultInspectDepth={1}
                    enableClipboard={false}
                    rootName={false}
                    theme="dark"
                  />
                )}
              </article>

              <article>
                <h3>Raw Model Reply</h3>
                <JsonViewer
                  value={response.raw}
                  defaultInspectDepth={2}
                  enableClipboard={false}
                  rootName={false}
                  theme="dark"
                />
              </article>
            </div>
          ) : (
            <p className="muted">Run a prompt to see the agent output.</p>
          )}
        </section>
      </main>
      <style jsx>{`
        .layout {
          min-height: 100vh;
          display: grid;
          grid-template-columns: minmax(320px, 420px) 1fr;
          gap: 1px;
          background: #1e293b;
        }

        .panel {
          padding: 2rem;
          background: rgba(15, 23, 42, 0.9);
        }

        .prompt-panel {
          border-right: 1px solid rgba(148, 163, 184, 0.2);
        }

        h1,
        h2,
        h3 {
          margin: 0 0 0.5rem;
        }

        .subtitle {
          margin: 0 0 1.5rem;
          color: #94a3b8;
          font-size: 0.95rem;
        }

        .prompt-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        input,
        textarea,
        select {
          width: 100%;
          resize: vertical;
          padding: 0.85rem 1rem;
          border-radius: 0.75rem;
          border: 1px solid rgba(148, 163, 184, 0.2);
          background: rgba(15, 23, 42, 0.7);
          color: inherit;
          font-size: 1rem;
        }

        button {
          border: none;
          border-radius: 9999px;
          padding: 0.75rem 1.5rem;
          background: linear-gradient(120deg, #0ea5e9, #8b5cf6);
          color: #0f172a;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s ease;
        }

        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .row {
          display: flex;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .field-group {
          flex: 1 1 180px;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .error {
          margin-top: 1rem;
          color: #f97316;
          font-weight: 500;
        }

        .response-panel {
          overflow-y: auto;
        }

        .response-content {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .assistant-message p,
        .assistant-message pre {
          white-space: pre-wrap;
          background: rgba(15, 23, 42, 0.6);
          padding: 1rem;
          border-radius: 0.75rem;
          border: 1px solid rgba(148, 163, 184, 0.15);
          margin: 0;
        }

        .idea-list,
        .hook-list,
        .score-list {
          display: grid;
          gap: 0.75rem;
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .idea-list li,
        .hook-list li,
        .score-list li {
          border: 1px solid rgba(148, 163, 184, 0.15);
          border-radius: 0.75rem;
          padding: 0.75rem 1rem;
          background: rgba(15, 23, 42, 0.6);
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }

        .idea-list li span {
          color: #cbd5f5;
        }

        .idea-list li em {
          font-style: normal;
          color: #38bdf8;
        }

        .hook-list li {
          flex-direction: row;
          align-items: center;
          gap: 0.75rem;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 9999px;
          padding: 0.2rem 0.75rem;
          background: rgba(14, 165, 233, 0.25);
          color: #38bdf8;
          font-weight: 600;
          font-size: 0.85rem;
        }

        .score-list li {
          gap: 0.5rem;
        }

        .score-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.75rem;
        }

        .score {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border-radius: 9999px;
          padding: 0.15rem 0.65rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .score-high {
          background: rgba(74, 222, 128, 0.2);
          color: #4ade80;
        }

        .score-medium {
          background: rgba(250, 204, 21, 0.2);
          color: #facc15;
        }

        .score-low {
          background: rgba(248, 113, 113, 0.2);
          color: #f87171;
        }

        .muted {
          color: #94a3b8;
        }

        @media (max-width: 960px) {
          .layout {
            grid-template-columns: 1fr;
          }

          .prompt-panel {
            border-right: none;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
          }
        }
      `}</style>
    </>
  );
}

