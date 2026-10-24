"use client";

import { MotionConfig } from "motion/react";
import { ThemeProvider } from "next-themes";

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <MotionConfig reducedMotion="user">
        <TooltipProvider>
          {children}
          <Toaster />
        </TooltipProvider>
      </MotionConfig>
    </ThemeProvider>
  );
}
