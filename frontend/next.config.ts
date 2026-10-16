import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Send API calls to Farhan's FastAPI backend in live mode (no CORS needed).
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/v1/:path*` }];
  },
  /* config options here */
  cacheComponents: true,
  devIndicators: false,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
