import type { ChatRequest, ChatResponse } from "./types";

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const resp = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!resp.ok) {
    // Backend already returns a ChatResponse-shaped body on errors via the proxy.
    const body = (await resp.json().catch(() => null)) as ChatResponse | null;
    if (body) return body;
    throw new Error(`Chat request failed: ${resp.status}`);
  }
  return (await resp.json()) as ChatResponse;
}

/**
 * Picks the best available image URL for a card.
 * Falls back through the Scryfall size ladder.
 */
export function cardImage(
  card: { image_uris?: { normal?: string; large?: string; small?: string; png?: string } },
  size: "small" | "normal" | "large" = "normal",
): string | undefined {
  const u = card.image_uris;
  if (!u) return undefined;
  return u[size] ?? u.normal ?? u.large ?? u.small ?? u.png;
}
