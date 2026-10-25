"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Stethoscope } from "lucide-react";

import { EvidenceList } from "@/components/EvidenceList";
import { Skeleton } from "@/components/ui/skeleton";
import { MaternalQuickCheck } from "@/components/MaternalQuickCheck";
import { UrgentTakeover } from "@/components/motion/UrgentTakeover";
import { GestationBar } from "@/components/viz/GestationBar";
import { RiskGauge } from "@/components/viz/RiskGauge";
import { TrendBand, type Band } from "@/components/viz/TrendBand";
import { api } from "@/lib/api";
import { AGENT_COLOR, AGENT_LABEL } from "@/lib/labels";
import type { components } from "@/types/openapi";

type AgentResult = components["schemas"]["AgentResult"];
type Analysis = components["schemas"]["AnalyzeResponse"];
type Chart = components["schemas"]["ChartSpec"];
type AncStep = { week: number; due: boolean; done: boolean };

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

function MaternalCharts({ r }: { r: AgentResult }) {
  const chart = (id: string): Chart | undefined => r.charts.find((c) => c.id === id);
  const gest = chart("gestation")?.data[0] as { week: number; total: number; trimester: number } | undefined;
  const bp = chart("bp_trend");
  const hb = chart("hb_trend");
  const anc = (r.stats.anc as AncStep[] | undefined) ?? [];
  const bpBands = (bp?.meta?.bands as { systolic: number; label: string }[] | undefined) ?? [];
  const hbBands = (hb?.meta?.bands as { max: number; label: string }[] | undefined) ?? [];
  const bands: Band[] = bpBands.length === 2
    ? [{ from: bpBands[0].systolic, to: bpBands[1].systolic, tone: "watch", label: bpBands[0].label },
       { from: bpBands[1].systolic, to: 200, tone: "urgent", label: bpBands[1].label }]
    : [];
  const hbB: Band[] = hbBands.length === 2
    ? [{ from: hbBands[1].max, to: hbBands[0].max, tone: "watch", label: hbBands[0].label },
       { from: 0, to: hbBands[1].max, tone: "urgent", label: hbBands[1].label }]
    : [];
  return (
    <>
      {gest && <Card title="Your pregnancy"><GestationBar week={gest.week} total={gest.total} trimester={gest.trimester} /></Card>}
      {bp && bp.data.length > 0 && (
        <Card title="Blood pressure">
          <TrendBand
            data={bp.data} bands={bands} unit="mmHg" domain={[60, 180]}
            series={[{ key: "systolic", label: "Systolic", color: "var(--agent-maternal)" },
                     { key: "diastolic", label: "Diastolic", color: "var(--secondary)" }]}
            summary={`Blood pressure over ${bp.data.length} readings, with raised and severe bands`}
          />
        </Card>
      )}
      {hb && hb.data.length > 0 && (
        <Card title="Haemoglobin">
          <TrendBand
            data={hb.data} bands={hbB} unit="g/dL" domain={[5, 14]}
            series={[{ key: "value", label: "Haemoglobin", color: "var(--agent-maternal)" }]}
            summary={`Haemoglobin over ${hb.data.length} readings, with low and severe bands`}
          />
        </Card>
      )}
      {anc.length > 0 && (
        <Card title="Antenatal visits">
          <ol className="grid gap-1 sm:grid-cols-2">
            {anc.map((a) => (
              <li key={a.week} className="flex min-h-11 items-center gap-3 rounded-xl px-2 text-sm">
                <span aria-hidden className="grid size-6 place-items-center rounded-full border text-xs"
                  style={a.done ? { background: "var(--status-ok)", color: "white", borderColor: "transparent" } : undefined}>
                  {a.done ? "✓" : ""}
                </span>
                Around week {a.week}
                <span className="ml-auto text-xs text-muted-foreground">
                  {a.done ? "Done" : a.due ? "Due" : "Upcoming"}
                </span>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </>
  );
}

export function AgentView({ name }: { name: string }) {
  const router = useRouter();
  const [r, setR] = useState<AgentResult | null>(null);
  const [failed, setFailed] = useState(false);
  const [urgent, setUrgent] = useState<string[] | null>(null);

  useEffect(() => {
    api<AgentResult>(`/agents/${name}`)
      .then(setR)
      .catch((e) => (e?.status === 401 ? router.replace("/") : setFailed(true)));
  }, [name, router]);

  function onAnalysis(a: Analysis) {
    const fresh = a.results.find((x) => x.agent === name);
    if (fresh) setR(fresh);
    if (a.routing.urgent) setUrgent(a.routing.urgent_reasons);
  }

  const gauges = r?.charts.filter((c) => c.kind === "gauge") ?? [];

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-5 px-4 py-10">
      {urgent && <UrgentTakeover reasons={urgent} onDismiss={() => setUrgent(null)} />}
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

          {r.agent === "maternal" && <MaternalCharts r={r} />}

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

          {r.agent === "maternal" && <MaternalQuickCheck onAnalysis={onAnalysis} />}

          <p className="text-xs text-muted-foreground">
            Awareness only. This is not a diagnosis. Consider discussing these patterns with a doctor.
          </p>
        </>
      )}
    </main>
  );
}
