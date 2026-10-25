"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Download, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

type Report = { report_id: number; url: string; summary: { text: string; source: string } };
type Lang = "en" | "hi";

export default function ReportPage() {
  const router = useRouter();
  const [lang, setLang] = useState<Lang>("en");
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      setReport(await api<Report>("/report", { method: "POST", body: JSON.stringify({ lang }) }));
    } catch (e) {
      if ((e as { status?: number })?.status === 401) router.replace("/");
      else setError("We could not build the report. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 px-4 py-10">
      <Link href="/hub" className="inline-flex min-h-11 items-center gap-1 text-sm underline">
        <ArrowLeft className="size-4" aria-hidden /> Back to your hub
      </Link>

      <section className="rounded-[20px] bg-card p-6 shadow-(--shadow-card)">
        <h1 className="font-heading text-2xl font-semibold">Doctor-ready report</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          A one to two page PDF of your last 90 days, with the evidence behind each pattern, to bring to a
          visit. Awareness only, not a diagnosis.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <div role="group" aria-label="Report language" className="inline-flex rounded-full bg-muted p-1">
            {(["en", "hi"] as const).map((l) => (
              <button
                key={l}
                type="button"
                aria-pressed={lang === l}
                onClick={() => setLang(l)}
                className={`min-h-11 rounded-full px-4 text-sm ${lang === l ? "bg-card font-semibold shadow-sm" : ""}`}
              >
                {l === "en" ? "English" : "हिन्दी"}
              </button>
            ))}
          </div>
          <Button onClick={generate} disabled={busy} className="min-h-11">
            <FileText className="size-4" aria-hidden /> {busy ? "Building your report…" : "Generate report"}
          </Button>
          {report && (
            <a
              href={report.url}
              download
              className="inline-flex min-h-11 items-center gap-2 text-sm font-medium underline"
            >
              <Download className="size-4" aria-hidden /> Download PDF
            </a>
          )}
        </div>
        {error && <p role="alert" className="mt-3 text-sm text-destructive">{error}</p>}
      </section>

      {report && (
        <iframe
          title="Report preview"
          src={report.url}
          className="h-[80vh] w-full rounded-[20px] bg-card shadow-(--shadow-card)"
        />
      )}
    </main>
  );
}
