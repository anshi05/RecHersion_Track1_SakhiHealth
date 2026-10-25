"""Output filter for LLM text: awareness only, so no diagnosis, drug names, doses or orders."""
import re

CONDITIONS = (
    r"pcos|pcod|polycystic|endometriosis|menopause|perimenopause|pre-?eclampsia|eclampsia|"
    r"gestational diabetes|diabetes|anaemia|anemia|thyroid|hypothyroid|hyperthyroid|cancer|pregnan\w+"
)
DRUGS = (
    r"metformin|ibuprofen|paracetamol|acetaminophen|naproxen|aspirin|clomiphene|letrozole|"
    r"spironolactone|progesterone|progestin|estrogen|oestrogen|estradiol|levothyroxine|"
    r"hormone (?:replacement )?therapy|hrt|oral contraceptive|birth control pill|"
    r"iron tablets?|folic acid|antibiotics?|painkillers?|supplements?"
)

BANNED: dict[str, re.Pattern[str]] = {
    "diagnosis": re.compile(
        rf"\b(?:you|she)\s+(?:definitely |probably |likely |clearly )?"
        rf"(?:have|has|are suffering from|suffer from|are diagnosed with|were diagnosed with)"
        rf"\s+(?:\w+\s+){{0,3}}(?:{CONDITIONS})\b"
        rf"|\byour diagnosis\b|\bdiagnosed with\b|\bthis is (?:definitely |clearly )?(?:{CONDITIONS})\b"
        rf"|\bconfirm(?:s|ed)? (?:that )?(?:you|she)\b",
        re.I,
    ),
    "dose": re.compile(
        r"\b\d+(?:\.\d+)?\s?(?:mg|mcg|µg|ug|ml|iu|g|tablets?|pills?|capsules?)\b"
        r"|\b(?:once|twice|thrice)\s+(?:a|per)\s+day\b|\b(?:once|twice) daily\b|\bdosage?\b",
        re.I,
    ),
    "drug": re.compile(rf"\b(?:{DRUGS})\b", re.I),
    "order": re.compile(
        r"\b(?:you|she)\s+(?:should|must|need to|have to)\s+(?:take|start|stop|skip|begin|use)\b"
        r"|\b(?:take|start|stop)\s+(?:taking\s+)?(?:this|these|the)\s+(?:medicine|medication|drug|treatment)\b"
        r"|\bprescri(?:be|bed|ption)\b",
        re.I,
    ),
}


def check(text: str) -> list[str]:
    """Return the names of violated guardrails; empty list means the text is safe to show."""
    if not text or not text.strip():
        return ["empty"]
    return [name for name, pattern in BANNED.items() if pattern.search(text)]


def is_safe(text: str) -> bool:
    return not check(text)
