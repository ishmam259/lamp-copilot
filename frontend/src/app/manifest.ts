import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "LaMP · Pharmacy finance",
    short_name: "LaMP",
    description: "Cash ahead, expiring stock, and the cheapest way to fund the next order.",
    start_url: "/",
    display: "standalone",
    background_color: "#eef1f3",
    theme_color: "#1e5bb8",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
