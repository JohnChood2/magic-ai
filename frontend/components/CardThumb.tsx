"use client";

import type { Card } from "@/lib/types";
import { cardImage } from "@/lib/api";

interface Props {
  card: Card;
  size?: "small" | "normal" | "large";
}

export default function CardThumb({ card, size = "normal" }: Props) {
  const src = cardImage(card, size);
  if (!src) {
    return (
      <div className="flex h-[340px] w-[245px] items-center justify-center rounded-lg border border-stone-300 p-3 text-center text-sm text-stone-500 dark:border-stone-700">
        {card.name}
      </div>
    );
  }
  return (
    <a
      href={card.scryfall_uri ?? "#"}
      target="_blank"
      rel="noreferrer"
      className="block transition hover:scale-[1.02]"
      title={card.name}
    >
      {/* Plain img avoids next/image config friction; switch to next/image later. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={card.name}
        loading="lazy"
        className="rounded-lg shadow-sm"
        width={245}
        height={340}
      />
    </a>
  );
}
