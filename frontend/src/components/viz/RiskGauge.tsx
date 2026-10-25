"use client";

import { useId } from "react";
import { motion, useReducedMotion } from "motion/react";
import { CircleAlert, CircleCheck, CircleHelp } from "lucide-react";

import { CountUp } from "@/components/motion/CountUp";
import { BAND_LABEL } from "@/lib/labels";
import { dur, ease } from "@/lib/motion";

const R = 80;
const C = 100;
const START = 150; // degrees, 240° sweep ending at 30° (guide §8.4)
const SWEEP = 240;

function point(deg: number): [number, number] {
  const a = (deg * Math.PI) / 180;
  return [C + R * Math.cos(a), C + R * Math.sin(a)];
}

const [x0, y0] = point(START);
const [x1, y1] = point(START + SWEEP);
const ARC = `M ${x0} ${y0} A ${R} ${R} 0 1 1 ${x1} ${y1}`;

const BAND_ICON = { low: CircleCheck, moderate: CircleHelp, high: CircleAlert } as const;

export function RiskGauge({ score, band, label }: { score: number; band: string; label: string }) {
  const gid = useId();
  const reduce = useReducedMotion();
  const clamped = Math.min(1, Math.max(0, score));
  const [tx, ty] = point(START + SWEEP * clamped);
  const Icon = BAND_ICON[band as keyof typeof BAND_ICON] ?? CircleHelp;
  const pct = Math.round(clamped * 100);

  return (
    <figure className="flex flex-col items-center" role="img" aria-label={`${label}: ${pct} out of 100, ${BAND_LABEL[band] ?? band} band`}>
      <div className="relative w-full max-w-[240px]">
      <svg viewBox="0 0 200 170" className="w-full" aria-hidden>
        <defs>
          <linearGradient id={gid} x1="0" y1="1" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--status-ok)" />
            <stop offset="55%" stopColor="var(--status-watch)" />
            <stop offset="100%" stopColor="var(--status-flag)" />
          </linearGradient>
        </defs>
        <path d={ARC} fill="none" stroke="var(--muted)" strokeWidth="14" strokeLinecap="round" />
        <motion.path
          d={ARC}
          fill="none"
          stroke={`url(#${gid})`}
          strokeWidth="14"
          strokeLinecap="round"
          initial={{ pathLength: reduce ? clamped : 0 }}
          animate={{ pathLength: clamped }}
          transition={{ duration: reduce ? 0 : dur.hero, ease: ease.out }}
        />
        <motion.circle
          cx={tx}
          cy={ty}
          r="7"
          fill="var(--card)"
          stroke="var(--foreground)"
          strokeWidth="3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: dur.base, delay: reduce ? 0 : dur.hero }}
        />
      </svg>
      <div className="absolute inset-x-0 top-[44%] flex flex-col items-center">
        <span className="font-heading text-5xl font-semibold leading-none">
          <CountUp value={pct} />
        </span>
        <span className="mt-1 inline-flex items-center gap-1 text-sm font-medium">
          <Icon className="size-4" aria-hidden />
          {BAND_LABEL[band] ?? band}
        </span>
      </div>
      </div>
      <figcaption className="mt-2 text-sm text-muted-foreground">{label}</figcaption>
    </figure>
  );
}
