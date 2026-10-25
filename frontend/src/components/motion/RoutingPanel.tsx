"use client";

import { motion, useReducedMotion } from "motion/react";
import { Sparkles } from "lucide-react";

import { AGENT_COLOR, AGENT_LABEL } from "@/lib/labels";
import { dur, ease, stagger } from "@/lib/motion";
import type { components } from "@/types/openapi";

type Routing = components["schemas"]["RoutingDecision"];

const AGENT_ORDER = ["health_story", "pcos_endo", "menopause", "maternal"] as const;
const ROW = 64; // px; connectors are drawn in a viewBox that matches this row height

/** Hub → agent routing (guide §8.6 #1): connectors draw, then each activated agent glows in order. */
export function RoutingPanel({ routing }: { routing: Routing }) {
  const reduce = useReducedMotion();
  const total = AGENT_ORDER.length;
  const hubY = (total * ROW) / 2;

  return (
    <div className="flex items-stretch gap-0" aria-label="How your data was routed to agents">
      <div className="flex w-20 shrink-0 items-center justify-center sm:w-28">
        <div className="flex size-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-(--shadow-card)">
          <Sparkles className="size-6" aria-hidden />
        </div>
      </div>

      <svg
        viewBox={`0 0 100 ${total * ROW}`}
        preserveAspectRatio="none"
        className="w-10 shrink-0 sm:w-24"
        style={{ height: total * ROW }}
        aria-hidden
      >
        {AGENT_ORDER.map((name) => {
          const i = routing.activated.indexOf(name);
          const on = i >= 0;
          const y = AGENT_ORDER.indexOf(name) * ROW + ROW / 2;
          return (
            <motion.path
              key={name}
              d={`M 0 ${hubY} C 50 ${hubY}, 50 ${y}, 100 ${y}`}
              fill="none"
              stroke={AGENT_COLOR[name]}
              strokeWidth={2}
              strokeLinecap="round"
              strokeDasharray={on ? undefined : "3 5"}
              vectorEffect="non-scaling-stroke"
              initial={{ pathLength: reduce || !on ? 1 : 0, opacity: on ? 1 : 0.4 }}
              animate={{ pathLength: 1, opacity: on ? 1 : 0.4 }}
              transition={{ duration: reduce ? 0 : dur.slow, ease: ease.out, delay: reduce ? 0 : i * stagger.routing }}
            />
          );
        })}
      </svg>

      <ul className="flex min-w-0 flex-1 flex-col">
        {AGENT_ORDER.map((name) => {
          const i = routing.activated.indexOf(name);
          const on = i >= 0;
          const delay = reduce ? 0 : i * stagger.routing + dur.slow;
          return (
            <motion.li
              key={name}
              style={{ height: ROW }}
              className="flex items-center"
              initial={{ opacity: on ? 0 : 0.4 }}
              animate={{ opacity: on ? 1 : 0.4 }}
              transition={{ duration: dur.base, delay: on ? delay : 0 }}
            >
              <motion.div
                className="w-full rounded-xl border px-3 py-1.5"
                style={{ borderColor: on ? AGENT_COLOR[name] : "var(--border)" }}
                initial={{ boxShadow: "0 0 0 0 transparent" }}
                animate={on ? { boxShadow: `0 0 18px 0 color-mix(in oklab, ${AGENT_COLOR[name]} 35%, transparent)` } : undefined}
                transition={{ duration: dur.slow, delay: on ? delay : 0 }}
              >
                <p className="truncate text-sm font-semibold">
                  {AGENT_LABEL[name]}
                  <span className="sr-only">{on ? " (activated)" : " (skipped)"}</span>
                </p>
                <p className="truncate text-xs text-muted-foreground" title={routing.reasons[name]}>
                  {routing.reasons[name]}
                </p>
              </motion.div>
            </motion.li>
          );
        })}
      </ul>
    </div>
  );
}
