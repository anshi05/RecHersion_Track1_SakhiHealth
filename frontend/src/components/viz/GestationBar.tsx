"use client";

import { motion, useReducedMotion } from "motion/react";

import { dur, ease } from "@/lib/motion";

const TRIMESTER = ["", "First trimester", "Second trimester", "Third trimester"];

export function GestationBar({ week, total = 40, trimester }: { week: number; total?: number; trimester: number }) {
  const reduce = useReducedMotion();
  const pct = Math.min(100, Math.max(0, (week / total) * 100));
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <p className="font-heading text-3xl font-semibold">Week {week}</p>
        <p className="text-sm text-muted-foreground">{TRIMESTER[trimester] ?? ""} · of {total} weeks</p>
      </div>
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={week}
        aria-label={`Pregnancy progress: week ${week} of ${total}`}
        className="relative h-3 overflow-hidden rounded-full bg-muted"
      >
        <motion.div
          className="h-full origin-left rounded-full"
          style={{ width: `${pct}%`, background: "var(--agent-maternal)" }}
          initial={reduce ? false : { scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: dur.hero, ease: ease.out }}
        />
      </div>
    </div>
  );
}
