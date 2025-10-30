import type { NextApiRequest, NextApiResponse } from 'next';

const AGENT_BASE_URL = process.env.AGENT_BASE_URL || 'http://localhost:8000';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  try {
    const response = await fetch(`${AGENT_BASE_URL}/run_agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(req.body)
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      return res.status(response.status).json(
        errorPayload || { detail: 'Agent call failed' }
      );
    }

    const data = await response.json();
    return res.status(200).json(data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return res.status(500).json({ detail: message });
  }
}

