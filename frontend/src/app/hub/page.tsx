"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { components } from "@/types/openapi";

type Session = components["schemas"]["SessionResponse"];

export default function Hub() {
  const router = useRouter();
  const [s, setS] = useState<Session | null>(null);

  useEffect(() => {
    api<Session>("/session").then(setS).catch(() => router.replace("/"));
  }, [router]);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 px-4 py-12">
      {s ? (
        <>
          <h1 className="font-heading text-4xl font-semibold tracking-tight">{s.profile.name}</h1>
          <p className="text-muted-foreground capitalize">{s.profile.life_stage.replace("_", " ")}</p>
          <p className="text-sm text-muted-foreground">Your health story is coming in the next phase.</p>
        </>
      ) : (
        <Skeleton className="h-24 rounded-[20px]" />
      )}
      <Link href="/" className="inline-flex min-h-11 items-center text-sm underline">Switch profile</Link>
    </main>
  );
}
