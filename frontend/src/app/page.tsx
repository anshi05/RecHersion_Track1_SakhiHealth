"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type Health = { status: string; llm: "live" | "fallback" };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Health>("/health").then(setHealth).catch(() => setFailed(true));
  }, []);

  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="font-heading text-4xl font-semibold tracking-tight">Sakhi Health</h1>
      <p className="text-muted-foreground">
        {failed
          ? "Backend unreachable"
          : health
            ? `API ${health.status} · AI ${health.llm}`
            : "Checking API…"}
      </p>
    </main>
  );
}
