"use client";

import { motion, useReducedMotion } from "motion/react";

import { dur, ease } from "@/lib/motion";
import type { components } from "@/types/openapi";

type Day = components["schemas"]["DayPoint"];
type Cycle = components["schemas"]["CycleEvent"];

const W = 1000;
const FLOW_OPACITY: Record<string, number> = { light: 0.35, medium: 0.65, heavy: 1 };
const DAY = 86_400_000;

export function CycleTimeline({ days, cycles }: { days: Day[]; cycles: Cycle[] }) {
  const reduce = useReducedMotion();
  if (days.length < 2) return <p className="text-sm text-muted-foreground">No cycle data yet.</p>;

  const t0 = Date.parse(days[0].date);
  const span = Date.parse(days[days.length - 1].date) - t0 || DAY;
  const x = (d: string) => 8 + ((Date.parse(d) - t0) / span) * (W - 16);
  const dayW = Math.max(2, ((W - 16) / days.length) * 0.9);
  const lastX = x(days[days.length - 1].date);
  const pain = days.filter((d) => d.pain_level !== null);
  const path = pain
    .map((d, i) => `${i ? "L" : "M"}${x(d.date).toFixed(1)} ${(150 - (d.pain_level! / 10) * 56).toFixed(1)}`)
    .join(" ");
  const completed = cycles.filter((c) => c.length_days).length;

  return (
    <div className="overflow-x-auto">
      <svg
        viewBox={`0 0 ${W} 172`}
        className="w-full min-w-[640px]"
        role="img"
        aria-label={`Cycle timeline: ${completed} completed cycles with pain overlay`}
      >
        {cycles.map((c, i) => {
          const next = cycles[i + 1];
          const x0 = x(c.start_date);
          const x1 = next ? x(next.start_date) : lastX;
          return (
            <g key={c.id}>
              <motion.rect
                x={x0}
                y={8}
                width={Math.max(x1 - x0 - 3, 4)}
                height={30}
                rx={9}
                fill="var(--agent-health-story)"
                fillOpacity={0.18}
                stroke="var(--agent-health-story)"
                strokeWidth={1.5}
                style={{ transformBox: "fill-box", transformOrigin: "left" }}
                initial={reduce ? { opacity: 0 } : { scaleX: 0, opacity: 0 }}
                whileInView={{ scaleX: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: dur.slow, ease: ease.out, delay: reduce ? 0 : i * 0.12 }}
              />
              {c.length_days && x1 - x0 > 40 && (
                <text x={(x0 + x1) / 2} y={28} textAnchor="middle" fontSize={14} fontWeight={600} fill="var(--foreground)">
                  {c.length_days} d
                </text>
              )}
            </g>
          );
        })}
        <motion.g
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: dur.slow, delay: reduce ? 0 : 0.8 }}
        >
          {days
            .filter((d) => d.flow in FLOW_OPACITY)
            .map((d) => (
              <rect key={d.date} x={x(d.date)} y={50} width={dayW} height={20} rx={2} fill="var(--accent)" fillOpacity={FLOW_OPACITY[d.flow]}>
                <title>{`${d.date}: ${d.flow} flow`}</title>
              </rect>
            ))}
        </motion.g>
        <line x1={8} x2={W - 8} y1={150} y2={150} stroke="var(--border)" />
        {path && (
          <motion.path
            d={path}
            fill="none"
            stroke="var(--primary)"
            strokeWidth={2}
            strokeLinejoin="round"
            initial={reduce ? { opacity: 0 } : { pathLength: 0 }}
            whileInView={reduce ? { opacity: 1 } : { pathLength: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 1.1, ease: ease.out, delay: reduce ? 0 : 0.4 }}
          />
        )}
        <text x={8} y={86} fontSize={11} fill="var(--muted-foreground)">Period days</text>
        <text x={W - 8} y={86} fontSize={11} textAnchor="end" fill="var(--primary)">Pain (0-10)</text>
        <text x={8} y={168} fontSize={11} fill="var(--muted-foreground)">{days[0].date}</text>
        <text x={W - 8} y={168} fontSize={11} textAnchor="end" fill="var(--muted-foreground)">
          {days[days.length - 1].date}
        </text>
      </svg>
    </div>
  );
}
