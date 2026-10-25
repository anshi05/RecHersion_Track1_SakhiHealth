import { RULE_LABEL } from "@/lib/labels";
import type { components } from "@/types/openapi";

type Evidence = components["schemas"]["Evidence"];

/** Every flag shows the rule that fired and the facts behind it (guide: explainable). */
export function EvidenceList({ items }: { items: Evidence[] }) {
  if (!items.length) {
    return <p className="text-sm text-muted-foreground">No patterns stood out in your logs.</p>;
  }
  return (
    <ul className="grid gap-3">
      {items.map((e) => (
        <li key={e.rule} className="rounded-xl bg-muted/50 p-3">
          <div className="flex items-baseline justify-between gap-2">
            <p className="font-medium">{RULE_LABEL[e.rule] ?? e.rule}</p>
            <code className="shrink-0 text-xs text-muted-foreground">{e.rule}</code>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">{e.detail}</p>
        </li>
      ))}
    </ul>
  );
}
