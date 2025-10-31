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

export default function Home() {
  const [prompt, setPrompt] = useState('Plan three TikTok ideas for eco-friendly skincare.');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/agent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
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
            <label htmlFor="prompt">Prompt</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={6}
              placeholder="Describe the marketing task..."
            />

            <button type="submit" disabled={isLoading || !prompt.trim()}>
              {isLoading ? 'Thinking…' : 'Run Agent'}
            </button>
          </form>

          {error && <p className="error">{error}</p>}
        </section>

        <section className="panel response-panel">
          <h2>Assistant Response</h2>
          {response ? (
            <div className="response-content">
              <article className="assistant-message">
                <h3>Message</h3>
                <pre>{response.message.content}</pre>
              </article>

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
          gap: 0.75rem;
        }

        textarea {
          resize: vertical;
          padding: 1rem;
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

        .assistant-message pre {
          white-space: pre-wrap;
          background: rgba(15, 23, 42, 0.6);
          padding: 1rem;
          border-radius: 0.75rem;
          border: 1px solid rgba(148, 163, 184, 0.15);
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

