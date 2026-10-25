"use client";

import { useEffect, useRef } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Phone, TriangleAlert } from "lucide-react";

import { dur, ease } from "@/lib/motion";

/** Full-screen red state for danger signs or severe readings (guide §8.6). Text only, no LLM. */
export function UrgentTakeover({ reasons, onDismiss }: { reasons: string[]; onDismiss?: () => void }) {
  const reduce = useReducedMotion();
  const first = useRef<HTMLAnchorElement>(null);
  const last = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    first.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onDismiss?.();
      if (e.key !== "Tab") return;
      // Keep focus inside the takeover.
      const els = [first.current, ...(last.current ? [last.current] : [])].filter(Boolean) as HTMLElement[];
      const all = [...els];
      document.querySelectorAll<HTMLElement>("[data-urgent-focus]").forEach((n) => all.includes(n) || all.push(n));
      const i = all.indexOf(document.activeElement as HTMLElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); all[all.length - 1]?.focus(); }
      else if (!e.shiftKey && i === all.length - 1) { e.preventDefault(); all[0]?.focus(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  return (
    <motion.div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="urgent-title"
      className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-6 overflow-y-auto p-6 text-center text-white"
      style={{ background: "var(--status-urgent)" }}
      initial={reduce ? false : { opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: dur.base, ease: ease.out }}
    >
      <TriangleAlert className="size-14" aria-hidden />
      <h1 id="urgent-title" className="max-w-xl font-heading text-3xl font-semibold leading-snug">
        Please get medical help now
      </h1>
      <ul className="max-w-xl text-lg">
        {reasons.map((r) => <li key={r}>{r}</li>)}
      </ul>
      <div className="flex w-full max-w-md flex-col gap-3">
        <a
          ref={first}
          href="tel:108"
          data-urgent-focus
          className="inline-flex min-h-16 items-center justify-center gap-3 rounded-2xl bg-white px-6 text-2xl font-semibold text-red-700 focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-white"
        >
          <Phone className="size-6" aria-hidden /> Call 108 (ambulance)
        </a>
        <a
          href="tel:112"
          data-urgent-focus
          className="inline-flex min-h-16 items-center justify-center gap-3 rounded-2xl border-2 border-white px-6 text-2xl font-semibold focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-white"
        >
          <Phone className="size-6" aria-hidden /> Call 112 (emergency)
        </a>
      </div>
      <p className="max-w-md text-sm opacity-90">
        Nearest facility: <em>coming soon (placeholder)</em>. Go to the nearest hospital or ask someone to take you.
        This is not a diagnosis; a doctor must assess you.
      </p>
      {onDismiss && (
        <button ref={last} type="button" data-urgent-focus onClick={onDismiss} className="min-h-11 text-sm underline">
          I have sought help, close this
        </button>
      )}
    </motion.div>
  );
}
