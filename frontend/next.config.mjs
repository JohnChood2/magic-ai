/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    // Scryfall serves card images from these hosts. Next/Image needs them whitelisted.
    remotePatterns: [
      { protocol: "https", hostname: "cards.scryfall.io" },
      { protocol: "https", hostname: "c1.scryfall.com" },
      { protocol: "https", hostname: "c2.scryfall.com" },
      { protocol: "https", hostname: "c3.scryfall.com" },
    ],
  },
};

export default nextConfig;
