"use client";

import { useEffect, useRef } from "react";
import { animate, useReducedMotion } from "motion/react";

import { dur, ease } from "@/lib/motion";

export function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
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
