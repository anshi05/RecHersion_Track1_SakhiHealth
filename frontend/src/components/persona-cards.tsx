"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, useReducedMotion } from "motion/react";
import { AlertCircle, Baby, Flower2, Sprout } from "lucide-react";

import { PersonaTransition } from "@/components/motion/PersonaTransition";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { dur, ease, stagger } from "@/lib/motion";
import type { components } from "@/types/openapi";

type Persona = components["schemas"]["Persona"];
type SwitchResponse = components["schemas"]["SwitchResponse"];

const STAGE: Record<string, { label: string; Icon: typeof Sprout; glow: string }> = {
  reproductive: { label: "Reproductive years", Icon: Sprout, glow: "var(--agent-pcos_endo, var(--primary))" },
  perimenopausal: { label: "Perimenopause", Icon: Flower2, glow: "var(--accent)" },
  pregnant: { label: "Pregnancy", Icon: Baby, glow: "var(--secondary)" },
};

export function PersonaCards() {
  const router = useRouter();
  const reduce = useReducedMotion();
  const [personas, setPersonas] = useState<Persona[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Persona | null>(null);

  const load = useCallback(() => {
    api<Persona[]>("/personas")
      .then((r) => {
        setError(null);
        setPersonas(r);
      })
      .catch(() => setError("Could not load personas."));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  async function choose(p: Persona) {
    if (pending) return;
    try {
      await api<SwitchResponse>("/session/switch", {
        method: "POST",
        body: JSON.stringify({ persona_key: p.key }),
      });
      setPending(p);
    } catch {
      setError("Could not open this profile. Please try again.");
    }
  }

  const onDone = useCallback(() => router.push("/hub"), [router]);

  return (
    <>
      <div aria-live="polite" className="grid w-full max-w-4xl gap-4 sm:grid-cols-3">
        {error && (
          <div className="col-span-full flex items-center justify-center gap-2 text-sm text-[var(--status-flag)]">
            <AlertCircle className="size-4" aria-hidden /> {error}
            <button onClick={load} className="min-h-11 px-3 underline">Retry</button>
          </div>
        )}
        {!personas && !error && [0, 1, 2].map((i) => <Skeleton key={i} className="h-44 rounded-[20px]" />)}
        {personas?.map((p, i) => {
          const s = STAGE[p.life_stage] ?? STAGE.reproductive;
          return (
            <motion.button
              key={p.key}
              type="button"
              onClick={() => choose(p)}
              initial={{ opacity: 0, y: reduce ? 0 : 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: dur.base, ease: ease.out, delay: i * stagger.list }}
              whileHover={reduce ? undefined : { y: -2 }}
              whileTap={reduce ? undefined : { scale: 0.98 }}
              className="relative min-h-44 overflow-hidden rounded-[20px] bg-card p-5 text-left shadow-[0_1px_2px_oklch(0_0_0/.04),0_8px_24px_oklch(0.5_0.1_300/.08)] outline-none focus-visible:ring-2 focus-visible:ring-primary dark:shadow-none dark:ring-1 dark:ring-white/10"
              style={{ backgroundImage: `radial-gradient(circle at 0% 0%, color-mix(in oklch, ${s.glow} 12%, transparent), transparent 60%)` }}
            >
              <s.Icon className="size-5 text-primary" aria-hidden />
              <h2 className="mt-3 font-heading text-2xl font-semibold tracking-tight">{p.name}</h2>
              <p className="text-sm text-muted-foreground tabular-nums">
                {p.age} · {s.label}
              </p>
              <p className="mt-3 text-sm">{p.tagline}</p>
            </motion.button>
          );
        })}
      </div>
      <PersonaTransition personaKey={pending?.key ?? null} name={pending?.name} onDone={onDone} />
    </>
  );
}
