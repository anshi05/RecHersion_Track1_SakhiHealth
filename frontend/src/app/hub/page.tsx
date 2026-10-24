"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { DashboardStats } from "@/components/dashboard-stats";
import { Skeleton } from "@/components/ui/skeleton";
import { CycleTimeline } from "@/components/viz/CycleTimeline";
import { Heatmap, type HeatRow } from "@/components/viz/Heatmap";
import { api } from "@/lib/api";
import type { components } from "@/types/openapi";

type Session = components["schemas"]["SessionResponse"];
type AgentResult = components["schemas"]["AgentResult"];
type Timeline = components["schemas"]["TimelineResponse"];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
      <h2 className="mb-3 text-2xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

function HubSkeleton() {
  return (
    <div className="grid gap-4" aria-busy="true" aria-label="Loading your health story">
      <Skeleton className="h-28 rounded-[20px]" />
      <div className="grid gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-28 rounded-[20px]" />)}
      </div>
      <Skeleton className="h-64 rounded-[20px]" />
      <Skeleton className="h-52 rounded-[20px]" />
    </div>
  );
}

export default function Hub() {
  const router = useRouter();
  const [s, setS] = useState<Session | null>(null);
  const [story, setStory] = useState<AgentResult | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<Session>("/session")
      .then((sess) => {
        setS(sess);
        return Promise.all([
          api<AgentResult>("/agents/health_story").then(setStory),
          api<Timeline>("/timeline?days=365").then(setTimeline),
        ]);
      })
      .catch((e) => (e?.status === 401 ? router.replace("/") : setFailed(true)));
  }, [router]);

  const heat = story?.charts.find((c) => c.id === "symptom_heatmap");
  const dates = ((heat?.meta?.dates as string[] | undefined) ?? []);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-10">
      <header className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="font-heading text-4xl font-semibold tracking-tight">{s ? s.profile.name : <Skeleton className="h-10 w-40" />}</h1>
          {s && <p className="text-muted-foreground capitalize">{s.profile.life_stage.replace("_", " ")}</p>}
        </div>
        <Link href="/" className="inline-flex min-h-11 items-center text-sm underline">Switch profile</Link>
      </header>

      {failed ? (
        <p role="alert" className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
          We could not load your health story. Check that the API is running, then reload.
        </p>
      ) : !story || !timeline ? (
        <HubSkeleton />
      ) : (
        <>
          <section className="relative overflow-hidden rounded-[20px] bg-card p-6 shadow-(--shadow-card)">
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 opacity-[0.08]"
              style={{ background: "radial-gradient(circle at top left, var(--agent-health-story), transparent 60%)" }}
            />
            <p className="relative text-sm text-muted-foreground">Your health story</p>
            <p className="relative mt-1 max-w-2xl font-heading text-2xl font-semibold leading-snug">{story.headline}</p>
          </section>

          <DashboardStats result={story} />

          <Section title="Symptoms over time">
            <Heatmap rows={(heat?.data ?? []) as HeatRow[]} dates={dates} />
          </Section>

          <Section title="Your cycles">
            <CycleTimeline days={timeline.days} cycles={timeline.cycles} />
          </Section>

          <p className="text-xs text-muted-foreground">
            Awareness only. This is not a diagnosis. Consider discussing these patterns with a doctor.
          </p>
        </>
      )}
    </main>
  );
}
