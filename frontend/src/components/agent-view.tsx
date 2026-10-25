"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Stethoscope } from "lucide-react";

import { EvidenceList } from "@/components/EvidenceList";
import { Skeleton } from "@/components/ui/skeleton";
import { RiskGauge } from "@/components/viz/RiskGauge";
import { api } from "@/lib/api";
import { AGENT_COLOR, AGENT_LABEL } from "@/lib/labels";
import type { components } from "@/types/openapi";

type AgentResult = components["schemas"]["AgentResult"];

const GAUGE_LABEL: Record<string, string> = {
  pcos_gauge: "PCOS-related patterns",
  endo_gauge: "Endometriosis-related patterns",
};

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
      <h2 className="mb-3 text-xl font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function AgentView({ name }: { name: string }) {
  const router = useRouter();
  const [r, setR] = useState<AgentResult | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api<AgentResult>(`/agents/${name}`)
      .then(setR)
      .catch((e) => (e?.status === 401 ? router.replace("/") : setFailed(true)));
  }, [name, router]);

  const gauges = r?.charts.filter((c) => c.kind === "gauge") ?? [];

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-4 py-10">
      <Link href="/hub" className="inline-flex min-h-11 items-center gap-1 text-sm underline">
        <ArrowLeft className="size-4" aria-hidden /> Back to your hub
      </Link>

      {failed ? (
        <p role="alert" className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
          We could not load this section. Check that the API is running, then reload.
        </p>
      ) : !r ? (
        <div className="grid gap-4" aria-busy="true" aria-label="Loading">
          <Skeleton className="h-28 rounded-[20px]" />
          <Skeleton className="h-56 rounded-[20px]" />
          <Skeleton className="h-48 rounded-[20px]" />
        </div>
      ) : (
        <>
          <header className="relative overflow-hidden rounded-[20px] bg-card p-6 shadow-(--shadow-card)">
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0 opacity-[0.08]"
              style={{ background: `radial-gradient(circle at top left, ${AGENT_COLOR[r.agent]}, transparent 60%)` }}
            />
            <p className="relative text-sm text-muted-foreground">{AGENT_LABEL[r.agent]}</p>
            <h1 className="relative mt-1 max-w-2xl font-heading text-2xl font-semibold leading-snug">{r.headline}</h1>
          </header>

          {gauges.length > 0 && (
            <Card title="Pattern strength">
              <div className="grid gap-6 sm:grid-cols-2">
                {gauges.map((g) => {
                  const d = g.data[0] as { score: number; band: string };
                  return <RiskGauge key={g.id} score={d.score} band={d.band} label={GAUGE_LABEL[g.id] ?? g.id} />;
                })}
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Based on how many commonly associated patterns appear in your logs. It is not a diagnosis.
              </p>
            </Card>
          )}

          <Card title="Why we noticed this">
            <EvidenceList items={r.evidence} />
          </Card>

          {r.cards.map((c) => (
            <section
              key={c.key}
              className="rounded-[20px] border-l-4 bg-card p-5 shadow-(--shadow-card)"
              style={{ borderLeftColor: AGENT_COLOR[r.agent] }}
            >
              <h2 className="text-lg font-semibold">{c.title}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{c.body}</p>
            </section>
          ))}

          {(r.specialist || r.suggested_tests.length > 0 || r.questions_for_doctor.length > 0) && (
            <Card title="For your doctor visit">
              {r.specialist && (
                <p className="mb-3 flex items-center gap-2 text-sm">
                  <Stethoscope className="size-4" aria-hidden /> Consider seeing: <strong>{r.specialist}</strong>
                </p>
              )}
              {r.suggested_tests.length > 0 && (
                <>
                  <h3 className="text-sm font-semibold">Tests you could ask about</h3>
                  <ul className="mb-3 mt-1 list-disc pl-5 text-sm text-muted-foreground">
                    {r.suggested_tests.map((t) => <li key={t}>{t}</li>)}
                  </ul>
                </>
              )}
              {r.questions_for_doctor.length > 0 && (
                <>
                  <h3 className="text-sm font-semibold">Questions to bring</h3>
                  <ul className="mt-1 list-disc pl-5 text-sm text-muted-foreground">
                    {r.questions_for_doctor.map((q) => <li key={q}>{q}</li>)}
                  </ul>
                </>
              )}
            </Card>
          )}

          <p className="text-xs text-muted-foreground">
            Awareness only. This is not a diagnosis. Consider discussing these patterns with a doctor.
          </p>
        </>
      )}
    </main>
  );
}
