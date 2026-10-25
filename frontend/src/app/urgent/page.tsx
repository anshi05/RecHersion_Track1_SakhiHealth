"use client";

import { useRouter } from "next/navigation";

import { UrgentTakeover } from "@/components/motion/UrgentTakeover";

export default function UrgentPage() {
  const router = useRouter();
  return (
    <UrgentTakeover
      reasons={["Severe headache, blurred vision, fits, heavy bleeding or much less baby movement need help right away."]}
      onDismiss={() => router.back()}
    />
  );
}
