"use client";

import { useEffect, useRef } from "react";
import { animate, useReducedMotion } from "motion/react";
import { CircleAlert, CircleCheck, CircleHelp, TrendingDown, TrendingUp } from "lucide-react";

import { METRIC_LABEL, PHASE_LABEL, SYMPTOM_LABEL, correlationText } from "@/lib/labels";
import { dur, ease } from "@/lib/motion";
import type { components } from "@/types/openapi";

type AgentResult = components["schemas"]["AgentResult"];

export type Stats = {
  cycle: { count: number; mean?: number; min?: number; max?: number; lengths: number[] };
  phase_frequency: { phase: string; symptom: string; pct: number; n: number }[];
  deltas: { metric: string; recent: number; previous: number; delta: number; notable: boolean }[];
  correlations: { key: string; r: number; n: number }[];
  days_logged: number;
};

function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const reduce = useReducedMotion();
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (reduce) {
      el.textContent = value.toFixed(decimals);
      return;
    }
    const c = animate(0, value, {
      duration: dur.hero,
      ease: ease.out,
      onUpdate: (v) => (el.textContent = v.toFixed(decimals)),
    });
    return () => c.stop();
  }, [value, decimals, reduce]);
  return <span ref={ref} className="tabular-nums">{value.toFixed(decimals)}</span>;
}

function Tile({ label, children, note }: { label: string; children: React.ReactNode; note?: string }) {
  return (
    <div className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
      <p className="text-sm text-muted-foreground">{label}</p>
      <div className="mt-1 font-heading text-4xl font-semibold">{children}</div>
      {note && <p className="mt-1 text-sm text-muted-foreground">{note}</p>}
    </div>
  );
}

export function DashboardStats({ result }: { result: AgentResult }) {
  const s = result.stats as unknown as Stats;
  const c = s.cycle;
  const irregular = result.evidence.some((e) => e.rule === "cycle_long" || e.rule === "cycle_variability");
  const reg = !c.count
    ? { label: "Not enough cycles yet", Icon: CircleHelp, tone: "text-muted-foreground" }
    : irregular
      ? { label: "Irregular", Icon: CircleAlert, tone: "text-status-flag" }
      : { label: "Regular", Icon: CircleCheck, tone: "text-status-ok" };
  const notable = s.deltas.filter((d) => d.notable);

  return (
    <div className="grid gap-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <Tile label="Average cycle" note={c.count ? `${c.count} cycles, ${c.min}-${c.max} days` : "Needs two logged periods"}>
          {c.mean ? (<><CountUp value={c.mean} decimals={0} /><span className="text-xl"> days</span></>) : "-"}
        </Tile>
        <Tile label="Regularity">
          <span className={`inline-flex items-center gap-2 text-2xl ${reg.tone}`}>
            <reg.Icon className="size-6" aria-hidden />
            {reg.label}
          </span>
        </Tile>
        <Tile label="Days logged" note="in this window">
          <CountUp value={s.days_logged} />
        </Tile>
      </div>

      {(notable.length > 0 || s.correlations.length > 0) && (
        <div className="grid gap-4 md:grid-cols-2">
          <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
            <h3 className="text-lg font-semibold">Last 14 days vs the 14 before</h3>
            {notable.length ? (
              <ul className="mt-3 grid gap-2 text-sm">
                {notable.map((d) => (
                  <li key={d.metric} className="flex items-center justify-between gap-3">
                    <span>{METRIC_LABEL[d.metric] ?? d.metric}</span>
                    <span className="inline-flex items-center gap-1 tabular-nums">
                      {d.delta > 0 ? <TrendingUp className="size-4" aria-hidden /> : <TrendingDown className="size-4" aria-hidden />}
                      {d.delta > 0 ? "+" : ""}{d.delta.toFixed(1)}
                      <span className="sr-only">{d.delta > 0 ? "higher" : "lower"}</span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">No big changes recently.</p>
            )}
          </section>
          <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
            <h3 className="text-lg font-semibold">Patterns in your logs</h3>
            {s.correlations.length ? (
              <ul className="mt-3 grid gap-3 text-sm">
                {s.correlations.map((k) => (
                  <li key={k.key}>
                    {correlationText(k.key, k.r)}
                    <span className="block text-xs text-muted-foreground">r = {k.r} across {k.n} days</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">No clear patterns yet. Keep logging.</p>
            )}
          </section>
        </div>
      )}

      {s.phase_frequency.length > 0 && <PhaseBars rows={s.phase_frequency} />}
    </div>
  );
}

function PhaseBars({ rows }: { rows: Stats["phase_frequency"] }) {
  const phases = [...new Set(rows.map((r) => r.phase))];
  const symptoms = [...new Set(rows.map((r) => r.symptom))].filter((sym) =>
    rows.some((r) => r.symptom === sym && r.pct >= 20),
  );
  return (
    <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
      <h3 className="text-lg font-semibold">How often symptoms show up by cycle phase</h3>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[420px] text-sm">
          <thead>
            <tr className="text-left text-muted-foreground">
              <th className="py-1 pr-2 font-medium">Symptom</th>
              {phases.map((p) => <th key={p} className="px-2 py-1 font-medium">{PHASE_LABEL[p] ?? p}</th>)}
            </tr>
          </thead>
          <tbody>
            {symptoms.map((sym) => (
              <tr key={sym} className="border-t">
                <td className="py-1.5 pr-2">{SYMPTOM_LABEL[sym] ?? sym}</td>
                {phases.map((p) => {
                  const r = rows.find((x) => x.phase === p && x.symptom === sym);
                  return (
                    <td key={p} className="px-2 py-1.5 tabular-nums">
                      {r ? (
                        <span className="flex items-center gap-2">
                          <span className="h-2 rounded-full bg-primary/70" style={{ width: `${Math.max(r.pct * 0.5, 2)}px` }} />
                          {r.pct}%
                        </span>
                      ) : "-"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
