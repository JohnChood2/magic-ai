"use client";

import type { Card } from "@/lib/types";
import { cardImage } from "@/lib/api";

interface Props {
  cards: Card[];
  maxShown?: number;
}

/**
 * Bulleted list with a hover-image preview. README spec:
 * "display in a bulleted list with a hover effect to display images
 *  (up to a maximum count, like 20 cards)".
 *
 * The hover image is positioned absolutely so it floats over surrounding
 * content without nudging layout.
 */
export default function CardList({ cards, maxShown = 20 }: Props) {
  if (cards.length === 0) return null;
  const shown = cards.slice(0, maxShown);
  const extra = cards.length - shown.length;

  return (
    <div className="mt-2">
      <ul className="space-y-1 text-sm">
        {shown.map((c) => {
          const img = cardImage(c, "normal");
          return (
            <li key={c.id} className="relative">
              <a
                href={c.scryfall_uri ?? "#"}
                target="_blank"
                rel="noreferrer"
                className="underline decoration-dotted underline-offset-2 hover:text-violet-600"
              >
                {c.name}
              </a>
              {c.type_line ? (
                <span className="ml-2 text-stone-500">— {c.type_line}</span>
              ) : null}
              {img ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={img}
                  alt=""
                  className="card-hover-image"
                  style={{ left: "calc(100% + 12px)", top: "50%" }}
                  width={245}
                  height={340}
                />
              ) : null}
            </li>
          );
        })}
      </ul>
      {extra > 0 ? (
        <p className="mt-2 text-xs text-stone-500">
          …and {extra} more. Try narrowing your query, or open Scryfall for the full list.
        </p>
      ) : null}
    </div>
  );
}
