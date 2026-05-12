/**
 * Server-side proxy from the browser to the FastAPI /chat endpoint.
 *
 * Keeping this server-side means:
 *   - The browser never needs to know the backend URL or any secret.
 *   - We can layer auth here later without touching the chat component.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  const body = await req.text(); // forward raw — backend validates with Pydantic
  try {
    const resp = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      // Don't cache chat responses.
      cache: "no-store",
    });
    const text = await resp.text();
    return new NextResponse(text, {
      status: resp.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return NextResponse.json(
      {
        reply:
          "I couldn't reach the MagicGPT backend. Is the FastAPI server running on " +
          BACKEND_URL +
          "?",
        cards: [],
        stop_reason: "backend_unreachable",
      },
      { status: 502 },
    );
  }
}
