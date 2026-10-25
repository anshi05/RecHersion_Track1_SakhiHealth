import { Suspense } from "react";

import { AgentView } from "@/components/agent-view";
import { Skeleton } from "@/components/ui/skeleton";

async function Resolved({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  return <AgentView name={name} />;
}

export default function AgentPage({ params }: { params: Promise<{ name: string }> }) {
  return (
    <Suspense fallback={<Skeleton className="mx-auto mt-10 h-56 w-full max-w-3xl rounded-[20px]" />}>
      <Resolved params={params} />
    </Suspense>
  );
}
