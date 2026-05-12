"use client";

import type { Card } from "@/lib/types";
import CardThumb from "./CardThumb";

interface Props {
  cards: Card[];
}

/**
 * Compact grid for small result sets (≤ 4 cards). README spec:
 * "If list of cards is small (4 or less?) display card images".
 */
export default function CardGrid({ cards }: Props) {
  if (cards.length === 0) return null;
  return (
    <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((c) => (
        <CardThumb key={c.id} card={c} />
      ))}
    </div>
  );
}
