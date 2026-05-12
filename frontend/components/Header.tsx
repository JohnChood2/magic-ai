"use client";

import type { ChatMode } from "@/lib/types";

interface Props {
  mode?: ChatMode;
  onModeChange?: (m: ChatMode) => void;
}

/**
 * Top chrome — wordmark + mode toggle (cards | rules).
 * Rules mode is wired up in the UI but disabled until Phase 2 ships.
 */
export default function Header({ mode = "cards", onModeChange }: Props) {
  return (
    <header className="flex items-center justify-between border-b border-stone-200 px-4 py-3 dark:border-stone-800">
      <div>
        <h1 className="text-xl font-semibold">
          Magic<span className="text-violet-600">GPT</span>
        </h1>
        <p className="text-xs text-stone-500">
          Unofficial — MTG card search & Commander deck help
        </p>
      </div>
      <div className="flex rounded-md border border-stone-300 text-sm dark:border-stone-700">
        <button
          type="button"
          className={`px-3 py-1.5 ${
            mode === "cards"
              ? "bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900"
              : ""
          }`}
          onClick={() => onModeChange?.("cards")}
        >
          Cards
        </button>
        <button
          type="button"
          className="cursor-not-allowed px-3 py-1.5 text-stone-400"
          title="Rules Q&A is planned for Phase 2"
          disabled
        >
          Rules
        </button>
      </div>
    </header>
  );
}
