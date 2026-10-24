"use client";

import { useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";

import { SYMPTOM_LABEL } from "@/lib/labels";
import { dur, ease } from "@/lib/motion";

export type HeatRow = { key: string; levels: (number | null)[] };

const CAP = 0.9; // seconds, guide §8.6 #2

export function Heatmap({ rows, dates }: { rows: HeatRow[]; dates: string[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduce = useReducedMotion();
  const cols = dates.length;

  if (!rows.length || !cols) {
    return <p className="text-sm text-muted-foreground">Log a few days to see your symptom pattern.</p>;
  }
  return (
    <div ref={ref} role="img" aria-label={`Symptom heatmap, ${rows.length} symptoms over ${cols} days`}>
      <div className="overflow-x-auto pb-2">
        <div
          className="grid gap-y-[3px]"
          style={{ gridTemplateColumns: `7rem repeat(${cols}, minmax(9px, 1fr))`, minWidth: cols * 10 + 112 }}
        >
          {rows.map((row, r) => (
            <div key={row.key} className="contents">
              <span className="sticky left-0 z-10 bg-card pr-2 text-xs leading-[14px] text-muted-foreground">
                {SYMPTOM_LABEL[row.key] ?? row.key}
              </span>
              {row.levels.map((lv, c) => {
                const rest = lv === null ? 0.5 : 1;
                return (
                  <motion.span
                    key={c}
                    title={`${SYMPTOM_LABEL[row.key] ?? row.key}, ${dates[c]}: ${lv === null ? "not logged" : `${lv}/5`}`}
                    className="mx-px block h-[14px] rounded-[3px]"
                    style={{ background: lv === null ? "var(--muted)" : `var(--heat-${lv})` }}
                    initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.6 }}
                    animate={inView ? { opacity: rest, scale: 1 } : undefined}
                    transition={{
                      duration: dur.base,
                      ease: ease.out,
                      delay: reduce ? 0 : Math.min((r + c) * 0.008, CAP),
                    }}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
        <span>{dates[0]}</span>
        <span className="flex items-center gap-1" aria-hidden>
          Less
          {[0, 1, 2, 3, 4, 5].map((n) => (
            <i key={n} className="inline-block size-3 rounded-[3px]" style={{ background: `var(--heat-${n})` }} />
          ))}
          More
        </span>
        <span>{dates[cols - 1]}</span>
      </div>
    </div>
  );
}
