import type { Metadata, Viewport } from "next";
import { Barlow, Courier_Prime } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/app-shell";

const barlow = Barlow({
  variable: "--font-barlow",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const stamp = Courier_Prime({
  variable: "--font-stamp",
  subsets: ["latin"],
  weight: ["700"],
});

export const metadata: Metadata = {
  title: { default: "LaMP", template: "%s · LaMP" },
  description: "Your pharmacy's finance officer: cash ahead, expiring stock, and the cheapest way to fund the next order.",
  applicationName: "LaMP",
};

export const viewport: Viewport = {
  themeColor: "#1e5bb8",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${barlow.variable} ${stamp.variable} h-full antialiased`}>
      <body className="min-h-full">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
