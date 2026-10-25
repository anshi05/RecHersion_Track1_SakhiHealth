"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { components } from "@/types/openapi";

type Analysis = components["schemas"]["AnalyzeResponse"];
type Log = components["schemas"]["DailyLog"];
type Saved = { analysis?: Analysis | null };

export const DANGER_SIGNS: [string, string][] = [
  ["severe_headache", "Severe headache"],
  ["blurred_vision", "Blurred vision or flashing lights"],
  ["convulsions", "Convulsions or fits"],
  ["heavy_bleeding", "Heavy vaginal bleeding"],
  ["leaking_fluid", "Leaking fluid"],
  ["severe_abdominal_pain", "Severe abdominal pain"],
  ["reduced_fetal_movement", "Reduced or no baby movement"],
  ["high_fever", "High fever"],
  ["face_hand_swelling", "Swelling of face or hands with headache"],
  ["difficulty_breathing", "Difficulty breathing"],
];

const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/** Danger-sign checklist plus a blood pressure entry. Both return a fresh analysis (guide D5). */
export function MaternalQuickCheck({ onAnalysis }: { onAnalysis: (a: Analysis) => void }) {
  const [signs, setSigns] = useState<string[]>([]);
  const [sys, setSys] = useState("");
  const [dia, setDia] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const date = today();
      let analysis: Analysis | null | undefined;
      if (signs.length) {
        // The log endpoint upserts the whole day, so keep today's existing entries.
        const [existing] = await api<Log[]>(`/logs?from=${date}&to=${date}`);
        const base: Record<string, unknown> = { ...(existing ?? {}) };
        delete base.id;
        delete base.user_id;
        const saved = await api<Saved>("/logs", {
          method: "POST",
          body: JSON.stringify({ ...base, date, danger_signs: signs }),
        });
        analysis = saved.analysis;
      }
      if (sys && dia) {
        const saved = await api<Saved>("/measurements", {
          method: "POST",
          body: JSON.stringify({ date, type: "bp", value_1: Number(sys), value_2: Number(dia), unit: "mmHg" }),
        });
        analysis = saved.analysis;
      }
      if (analysis) onAnalysis(analysis);
    } catch {
      setError("We could not save that. If you feel unwell, call 108 or 112 now.");
    } finally {
      setBusy(false);
    }
  }

  const toggle = (k: string) => setSigns((s) => (s.includes(k) ? s.filter((x) => x !== k) : [...s, k]));

  return (
    <section className="rounded-[20px] bg-card p-5 shadow-(--shadow-card)">
      <h2 className="mb-1 text-xl font-semibold">Quick check</h2>
      <p className="mb-3 text-sm text-muted-foreground">
        Tick anything you are feeling today, or add a blood pressure reading.
      </p>
      <fieldset className="grid gap-1 sm:grid-cols-2">
        <legend className="sr-only">Danger signs</legend>
        {DANGER_SIGNS.map(([k, label]) => (
          <label key={k} className="flex min-h-11 items-center gap-3 rounded-xl px-2 text-sm hover:bg-muted/50">
            <input type="checkbox" className="size-5 accent-[var(--agent-maternal)]" checked={signs.includes(k)}
              onChange={() => toggle(k)} />
            {label}
          </label>
        ))}
      </fieldset>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="grid gap-1 text-sm">Systolic
          <input inputMode="numeric" value={sys} onChange={(e) => setSys(e.target.value.replace(/\D/g, ""))}
            className="min-h-11 w-24 rounded-xl border bg-background px-3" placeholder="120" />
        </label>
        <label className="grid gap-1 text-sm">Diastolic
          <input inputMode="numeric" value={dia} onChange={(e) => setDia(e.target.value.replace(/\D/g, ""))}
            className="min-h-11 w-24 rounded-xl border bg-background px-3" placeholder="80" />
        </label>
        <Button onClick={submit} disabled={busy || (!signs.length && !(sys && dia))} className="min-h-11 px-5">
          {busy ? "Checking…" : "Check now"}
        </Button>
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-destructive">{error}</p>}
    </section>
  );
}
