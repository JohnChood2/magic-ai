import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // MTG-flavored palette. Use sparingly; the chat UI should feel neutral.
        mtg: {
          white: "#fffbd5",
          blue: "#aae0fa",
          black: "#cbc2bf",
          red: "#f9aa8f",
          green: "#9bd3ae",
        },
      },
    },
  },
  plugins: [],
};

export default config;
