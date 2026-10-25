"use client";

import { CartesianGrid, Line, LineChart, ReferenceArea, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export type Band = { from: number; to: number; tone: "watch" | "urgent"; label: string };
export type Series = { key: string; label: string; color: string };

/** A trend line with shaded threshold bands (BP, haemoglobin). Bands are labelled, not colour-only. */
export function TrendBand({
  data,
  series,
  bands,
  unit,
  domain,
  summary,
}: {
  data: Record<string, unknown>[];
  series: Series[];
  bands: Band[];
  unit: string;
  domain: [number, number];
  summary: string;
}) {
  return (
    <figure role="img" aria-label={summary}>
      <div className="h-56 w-full" aria-hidden>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            {bands.map((b) => (
              <ReferenceArea
                key={b.label}
                y1={b.from}
                y2={b.to}
                fill={`var(--status-${b.tone})`}
                fillOpacity={b.tone === "urgent" ? 0.18 : 0.14}
                ifOverflow="hidden"
              />
            ))}
            <XAxis dataKey="date" tickFormatter={(d: string) => d.slice(5)} tick={{ fontSize: 11 }} minTickGap={24} />
            <YAxis domain={domain} tick={{ fontSize: 11 }} unit={` ${unit}`} width={64} />
            <Tooltip />
            {series.map((s) => (
              <Line key={s.key} type="monotone" dataKey={s.key} name={s.label} stroke={s.color} strokeWidth={2.5}
                dot={{ r: 3 }} isAnimationActive={false} connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {bands.map((b) => (
          <span key={b.label} className="inline-flex items-center gap-1.5">
            <span aria-hidden className="size-2.5 rounded-sm" style={{ background: `var(--status-${b.tone})` }} />
            {b.label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
