"use client";

import { useRef, useState } from "react";
import { sendChat } from "@/lib/api";
import type { Card, ChatMessage } from "@/lib/types";
import Message from "./Message";

interface AssistantTurn extends ChatMessage {
  cards?: Card[];
}

const STARTER_PROMPTS = [
  "Show me blue card-draw spells for a Commander deck.",
  "I'm building a Edgar Markov vampire tribal deck — recommend 5 must-include cards.",
  "Find creatures with flying and lifelink that cost 3 or less.",
  "What are good budget green ramp cards?",
];

export default function Chat() {
  const [messages, setMessages] = useState<AssistantTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function submit(text: string) {
    const userTurn: AssistantTurn = { role: "user", content: text };
    const next = [...messages, userTurn];
    setMessages(next);
    setDraft("");
    setSending(true);

    try {
      const resp = await sendChat({
        // Strip cards from history; the backend only needs role+content.
        messages: next.map(({ role, content }) => ({ role, content })),
        mode: "cards",
      });
      setMessages((m) => [
        ...m,
        { role: "assistant", content: resp.reply, cards: resp.cards },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            "Something went wrong reaching the backend. Try again in a moment.",
        },
      ]);
    } finally {
      setSending(false);
      // Scroll to bottom after the new message renders.
      requestAnimationFrame(() => {
        scrollRef.current?.scrollTo({
          top: scrollRef.current.scrollHeight,
          behavior: "smooth",
        });
      });
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (draft.trim() && !sending) submit(draft.trim());
    }
  }

  return (
    <div className="flex flex-1 flex-col">
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="mx-auto max-w-md space-y-3 text-center">
            <p className="text-sm text-stone-500">
              Ask about cards, archetypes, or Commander deck building.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {STARTER_PROMPTS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => submit(p)}
                  className="rounded-full border border-stone-300 px-3 py-1.5 text-xs hover:bg-stone-100 dark:border-stone-700 dark:hover:bg-stone-800"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} cards={m.cards} />
        ))}

        {sending ? (
          <Message role="assistant" content="Thinking…" />
        ) : null}
      </div>

      <form
        className="border-t border-stone-200 p-3 dark:border-stone-800"
        onSubmit={(e) => {
          e.preventDefault();
          if (draft.trim() && !sending) submit(draft.trim());
        }}
      >
        <div className="flex gap-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about a card, archetype, or deck…"
            rows={2}
            className="flex-1 resize-none rounded-lg border border-stone-300 bg-white p-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 dark:border-stone-700 dark:bg-stone-900"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !draft.trim()}
            className="self-end rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
