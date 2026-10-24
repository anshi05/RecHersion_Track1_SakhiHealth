import { PersonaCards } from "@/components/persona-cards";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-8 px-4 py-12 text-center">
      <div className="space-y-3">
        <h1 className="font-heading text-4xl font-semibold tracking-tight sm:text-5xl">Sakhi Health</h1>
        <p className="mx-auto max-w-md text-muted-foreground">
          Your health story, in one place. Choose a profile to explore patterns from their logs.
        </p>
      </div>
      <PersonaCards />
      <p className="text-xs text-muted-foreground">
        Awareness only. Not a diagnosis. Consider discussing patterns with a doctor.
      </p>
    </main>
  );
}
