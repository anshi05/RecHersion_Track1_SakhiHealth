/** English display labels (Hindi arrives in P11 via messages/). */
export const SYMPTOM_LABEL: Record<string, string> = {
  pain: "Pain", acne: "Acne", hirsutism: "Unwanted hair", hair_thinning: "Hair thinning",
  headache: "Headache", swelling: "Swelling", fatigue: "Fatigue", low_mood: "Low mood",
  hot_flashes: "Hot flashes", bloating: "Bloating", night_sweats: "Night sweats",
  joint_pain: "Joint pain", brain_fog: "Brain fog", vaginal_dryness: "Vaginal dryness", nausea: "Nausea",
};

export const METRIC_LABEL: Record<string, string> = {
  mood: "Mood", energy: "Energy", sleep_hours: "Sleep (h)", pain_level: "Pain",
  stress: "Stress", fatigue: "Fatigue",
};

export const PHASE_LABEL: Record<string, string> = {
  menstrual: "Period", follicular: "After period", ovulatory: "Mid-cycle", luteal: "Before next period",
};

/** Plain-language sentence for a reported correlation (a pattern, never a cause). */
export function correlationText(key: string, r: number): string {
  switch (key) {
    case "sleep_next_day_mood":
      return r > 0
        ? "After nights with more sleep, your next-day mood tends to be higher."
        : "After nights with more sleep, your next-day mood tends to be lower.";
    case "pain_cycle_day":
      return r < 0
        ? "Your pain tends to be higher early in the cycle."
        : "Your pain tends to be higher later in the cycle.";
    case "stress_headache":
      return r > 0
        ? "Headaches tend to be stronger on higher-stress days."
        : "Headaches tend to be weaker on higher-stress days.";
    default:
      return key;
  }
}
