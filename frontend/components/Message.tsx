"use client";

import type { Card, ChatRole } from "@/lib/types";
import CardGrid from "./CardGrid";
import CardList from "./CardList";

interface Props {
  role: ChatRole;
  content: string;
  cards?: Card[];
}

/**
 * Picks a card display layout based on the README's display rules:
 *   ≤ 4 cards  → grid
 *   > 4 cards  → bulleted list with hover image
 */
function CardDisplay({ cards }: { cards: Card[] }) {
  if (cards.length === 0) return null;
  return cards.length <= 4 ? <CardGrid cards={cards} /> : <CardList cards={cards} />;
}

export default function Message({ role, content, cards = [] }: Props) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[90%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-violet-600 text-white"
            : "bg-stone-100 text-stone-900 dark:bg-stone-800 dark:text-stone-100"
        }`}
      >
        <div className="whitespace-pre-wrap text-sm">{content}</div>
        {!isUser && cards.length > 0 ? <CardDisplay cards={cards} /> : null}
      </div>
    </div>
  );
}
