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

export const AGENT_LABEL: Record<string, string> = {
  health_story: "Health Story", pcos_endo: "PCOS & Endometriosis",
  menopause: "Menopause", maternal: "Maternal health",
};

/** Agent-id → CSS color token (guide §8.1). */
export const AGENT_COLOR: Record<string, string> = {
  health_story: "var(--agent-health-story)", pcos_endo: "var(--agent-pcos-endo)",
  menopause: "var(--agent-menopause)", maternal: "var(--agent-maternal)",
};

export const BAND_LABEL: Record<string, string> = { low: "Low", moderate: "Moderate", high: "High" };

export const RULE_LABEL: Record<string, string> = {
  cycle_long: "Long cycles", cycle_variability: "Variable cycle length",
  hirsutism_persistent: "Persistent unwanted hair growth", acne_persistent: "Persistent acne",
  pco_ultrasound: "Ultrasound finding", family_history_pcos: "Family history",
  bmi_elevated: "Body mass index", severe_period_pain: "Severe period pain",
  pain_interferes: "Pain interfering with daily life",
  dyspareunia_or_bowel_urinary: "Pain with intimacy or bowel/urinary symptoms",
  vasomotor_frequent: "Frequent hot flashes", night_sweats_frequent: "Frequent night sweats",
  sleep_short: "Short sleep", perimenopause_age_window: "Age window",
  bp_alert: "Raised blood pressure", anemia_low_hb: "Low haemoglobin",
  low_fetal_movement: "Fewer baby movements", anemia_severe: "Very low haemoglobin",
  rapid_weight_gain: "Rapid weight gain", anc_missed: "Antenatal visits behind schedule", swelling_with_headache: "Swelling with headache",
};
