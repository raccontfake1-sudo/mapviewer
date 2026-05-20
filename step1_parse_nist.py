import argparse
import csv
import re
from pathlib import Path

import pdfplumber

SYNONYM_GROUPS = [
    ["cybersecurity", "information security"],
    ["entity", "organization"],

    ["strategy", "policy", "objectives", "strategic direction",
     "leadership and commitment", "integration",
     "continuing suitability, adequacy and effectiveness"],

    ["identified, documented, and approved", "established"],
    ["developed", "managed", "performed"],

    ["legislative and regulatory requirements",
     "legal and regulatory requirements",
     "Legal, statutory, regulatory and contractual requirements",
     "interested parties requirements"],

    ["periodically", "regularly", "at planned intervals"],

    ["periodically reviewed", "reviewed",
     "reviewed at planned", "reviewed and updated"],

    ["head of the entity", "top management",
     "authorized official", "internal and external stakeholders"],

    ["in line with", "compatible"],

    ["department for cybersecurity", "responsibility and authority"],

    ["information and technology assets", "inventory",
     "technology assets", "information resources"],

    ["archiving and backup", "backup copies"],
    ["qualified saudi cybersecurity professionals", "adequate resources"],
    ["risk methodology and procedures", "standardized risk method"],
    ["continuity", "availability", "data accessibility"],
    ["response plans", "responses"],
    ["disaster recovery", "restoration"],
    ["asset inventory", "asset identification"],
    ["asset classification", "asset categorization", "data classification"],
    ["ownership assignment", "asset accountability"],
    ["identity management", "identity governance"],
    ["access control", "authorization control"],
    ["multi-factor authentication", "strong authentication"],
    ["least privilege", "minimal access rights"],
    ["segregation of duties", "role-based access control"],
    ["confidentiality", "data privacy"],
    ["integrity", "data integrity protection"],
    ["data protection controls", "data security safeguards"],
    ["vulnerability scanning", "threat and vulnerability identification"],
    ["risk classification", "risk analysis"],
    ["remediation plan", "risk treatment plan"],
    ["incident response", "incident handling"],
    ["threat detection", "event monitoring"],
    ["escalation procedure", "incident coordination"],
    ["containment measures", "mitigation actions"]
]

# Matches CSF 2.0 subcategory IDs, e.g., GV.OC-01
RE_SUBCAT = re.compile(r"\b([A-Z]{2}\.[A-Z]{2}-\d{2})\b\s*[:\-–]?\s*(.*)$")
RE_HEADER = re.compile(r"^(GOVERN|IDENTIFY|PROTECT|DETECT|RESPOND|RECOVER)\b", re.IGNORECASE)
RE_BULLET_ONLY = re.compile(r"^[o•◦·▪●]$")


def clean_line(s: str) -> str:
    s = (s or "").replace("\u00ad", "")  # soft hyphen
    s = s.replace("\uf0b7", "•")  # common PDF bullet glyph
    return " ".join(s.strip().split())


def normalize_control_text(s: str) -> str:
    # Remove inline bullet artifacts that pdfplumber often emits as a standalone token.
    # Example: "risk o management" -> "risk management"
    s = re.sub(r"\b([A-Za-z0-9]+)\s+[o•◦·▪●]\s+([A-Za-z0-9]+)\b", r"\1 \2", s)
    # Collapse duplicated punctuation spacing.
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_lines(pdf_path: Path) -> list[str]:
    lines: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            for raw in txt.splitlines():
                line = clean_line(raw)
                if not line:
                    continue
                if RE_BULLET_ONLY.match(line):
                    continue
                lines.append(line)
    return lines


def parse_nist_subcategories(lines: list[str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    current_id: str | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_id, current_parts
        if current_id:
            text = normalize_control_text(" ".join([p for p in current_parts if p]).strip())
            if text:
                rows.append((current_id, text))
        current_id = None
        current_parts = []

    for line in lines:
        m = RE_SUBCAT.search(line)
        if m:
            flush()
            current_id = m.group(1)
            rest = (m.group(2) or "").strip()
            current_parts = [rest] if rest else []
            continue

        if not current_id:
            continue

        # Stop at major function headers.
        if RE_HEADER.match(line):
            flush()
            continue

        # Skip obvious bullet list lines that are references, not control statements.
        if line.startswith(("•", "◦", "·", "▪", "●")):
            continue

        current_parts.append(line)

    flush()
    return rows


def write_csv(rows: list[tuple[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["control_ref", "control_text"])
        w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse NIST CSF PDF into control_ref/control_text CSV")
    parser.add_argument("--input", default="NIST.pdf", help="Path to NIST PDF")
    parser.add_argument("--output", default="nist.csv", help="Output CSV path")
    args = parser.parse_args()

    pdf_path = Path(args.input)
    output_path = Path(args.output)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Input file not found: {pdf_path}")

    lines = extract_lines(pdf_path)
    rows = parse_nist_subcategories(lines)
    write_csv(rows, output_path)
    print(f"Extracted {len(rows)} subcategories -> {output_path}")


if __name__ == "__main__":
    main()