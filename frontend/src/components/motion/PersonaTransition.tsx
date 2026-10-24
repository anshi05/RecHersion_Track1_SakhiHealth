"use client";

import { useEffect } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";

import { dur, ease } from "@/lib/motion";

const TINT: Record<string, string> = {
  priya: "oklch(0.72 0.14 300)",
  meena: "oklch(0.76 0.13 35)",
  sunita: "oklch(0.70 0.12 190)",
};

/** Full-screen tint wash shown while switching persona; calls onDone once covered. */
export function PersonaTransition({
  personaKey,
  name,
  onDone,
}: {
  personaKey: string | null;
  name?: string;
  onDone: () => void;
}) {
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!personaKey) return;
    const t = setTimeout(onDone, reduce ? 150 : 650);
    return () => clearTimeout(t);
  }, [personaKey, reduce, onDone]);

  return (
    <AnimatePresence>
      {personaKey && (
        <motion.div
          key={personaKey}
          role="status"
          aria-live="polite"
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: TINT[personaKey] ?? TINT.priya }}
          initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 1.04 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: dur.slow, ease: ease.out }}
        >
          <p className="font-heading text-4xl font-semibold tracking-tight text-background">
            {name ? `Opening ${name}'s story…` : "Loading…"}
          </p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
