/** Motion tokens (guide §8.5). Animate transform/opacity only. */
export const dur = { fast: 0.15, base: 0.25, slow: 0.4, hero: 0.7 } as const;

export const ease = {
  out: [0.16, 1, 0.3, 1],
  inOut: [0.65, 0, 0.35, 1],
} as const;

export const spring = {
  snappy: { type: "spring", stiffness: 420, damping: 30 },
  soft: { type: "spring", stiffness: 180, damping: 24 },
} as const;

/** Seconds between staggered children. */
export const stagger = { list: 0.06, heatmapRow: 0.09, routing: 0.35 } as const;
