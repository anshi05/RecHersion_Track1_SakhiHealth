import type { Metadata } from "next";
import {
  Fraunces,
  Noto_Sans_Devanagari,
  Noto_Serif_Devanagari,
  Plus_Jakarta_Sans,
} from "next/font/google";

import { Providers } from "@/components/providers";

import "./globals.css";

const jakarta = Plus_Jakarta_Sans({ variable: "--font-jakarta", subsets: ["latin"] });
const fraunces = Fraunces({ variable: "--font-fraunces", subsets: ["latin"], axes: ["opsz"] });
const notoSans = Noto_Sans_Devanagari({ variable: "--font-deva-sans", subsets: ["devanagari"] });
const notoSerif = Noto_Serif_Devanagari({ variable: "--font-deva-serif", subsets: ["devanagari"] });

export const metadata: Metadata = {
  title: "Sakhi Health",
  description: "A life-stage women's health companion that turns your logs into a health story.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${jakarta.variable} ${fraunces.variable} ${notoSans.variable} ${notoSerif.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
