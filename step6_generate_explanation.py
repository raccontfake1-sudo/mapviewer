import os
import re
import json
import time
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from groq import Groq


# ============================================================
# FULL STEP 6: GENERATE + REPAIR EXPLANATIONS IN ONE FILE
# WITH TEXT ENCODING CLEANUP
# ============================================================
#
# Input:
#   data/final_owl_ontology_refined_mappings.csv
#
# Output:
#   data/final_with_explanations_COMPLETE.csv
#
# This script:
#   1. Reads the ontology refined mapping file.
#   2. Fixes broken encoding such as â€œ and â€.
#   3. Fixes parser artifact text such as "The Details of the contribute".
#   4. Removes parent ECC controls.
#   5. Keeps the wide format.
#   6. Adds Commonality, Justification, and Differences after each mapping.
#   7. Uses GROQ to generate explanation text.
#   8. Automatically checks and repairs blanks.
#   9. Saves one complete final file.
# ============================================================


# ============================================================
# SYNONYM GROUPS
# ============================================================

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


# ============================================================
# LOGGER
# ============================================================

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


# ============================================================
# GROQ CLIENT
# ============================================================

def setup_groq_client():
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY was not found in your .env file.")

    return Groq(api_key=api_key)


# ============================================================
# TEXT CLEANING / ENCODING FIX
# ============================================================

def fix_text_encoding(text):
    """
    Fixes common mojibake / broken encoding issues caused by CSV and Excel reading.
    Example:
        â€œAuthorized Officialâ€ -> “Authorized Official”
    """

    if pd.isna(text):
        return text

    text = str(text)

    replacements = {
        "â€œ": "“",
        "â€": "”",
        "â€™": "’",
        "â€˜": "‘",
        "â€“": "–",
        "â€”": "—",
        "â€¦": "…",
        "Â": "",
        "â€": "”",
        "Ã©": "é",
        "Ã¨": "è",
        "Ã¡": "á",
        "Ã­": "í",
        "Ã³": "ó",
        "Ãº": "ú",
        "Ã±": "ñ",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text


def clean_control_text(text):
    """
    Cleans parsed ECC/NIST control text before sending it to GROQ
    and before saving it to the final output.
    """

    if pd.isna(text):
        return text

    text = str(text)

    # Fix encoding first.
    text = fix_text_encoding(text)

    # Fix common parser artifact from ECC parsing.
    text = text.replace(
        "The Details of the contribute to compliance with the relevant legislative and regulatory requirements.",
        "The control contributes to compliance with the relevant legislative and regulatory requirements."
    )

    text = text.replace(
        "The Details of contribute to compliance with the relevant legislative and regulatory requirements.",
        "The control contributes to compliance with the relevant legislative and regulatory requirements."
    )

    text = text.replace(
        "The Details of the contribute",
        "The control contributes"
    )

    text = text.replace(
        "The Details of contribute",
        "The control contributes"
    )

    # Fix other awkward extracted phrasing if repeated.
    text = text.replace(
        "The Details of the",
        "The control details"
    )

    text = text.replace(
        "The Details of",
        "The control details"
    )

    # Remove repeated spaces.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_dataframe_text_columns(df):
    """
    Applies encoding and parser cleanup to all object/text columns.
    """

    text_columns = [col for col in df.columns if df[col].dtype == "object"]

    for col in text_columns:
        df[col] = df[col].apply(clean_control_text)

    return df


# ============================================================
# GENERAL HELPERS
# ============================================================

def format_synonym_groups_for_prompt():
    return "\n".join([" = ".join(group) for group in SYNONYM_GROUPS])


def is_blank(value):
    if pd.isna(value):
        return True

    value = str(value).strip()

    if value == "":
        return True

    if value.lower() in ["nan", "none", "null"]:
        return True

    return False


def is_leaf_control(control_id):
    """
    Keeps detailed ECC controls only.

    Keeps:
        1.1.1
        1.10.3.1

    Removes:
        1
        1.1
        2.3
    """

    if pd.isna(control_id):
        return False

    control_id = str(control_id).strip()

    match = re.search(r"\d+(?:\.\d+)+", control_id)

    if not match:
        return False

    numeric_part = match.group(0)

    return numeric_part.count(".") >= 2


def remove_parent_controls(df):
    if "ECC id control" not in df.columns:
        raise ValueError("Column 'ECC id control' was not found.")

    return df[df["ECC id control"].apply(is_leaf_control)].copy()


def suffix(rank):
    return "" if rank == 1 else f" {rank}"


def get_columns(rank):
    s = suffix(rank)

    return {
        "nist_mapping": f"NIST mapping{s}",
        "nist_text": f"Text{s}",
        "dense": f"Dense{s}",
        "sparse": f"Sparse{s}",
        "hybrid": f"Hybrid{s}",
        "ontology": f"Ontology score{s}",
        "final": f"Final Score{s}",
        "confidence": f"Confidence match{s}",
        "commonality": f"Commonality{s}",
        "justification": f"Justification{s}",
        "differences": f"Differences{s}",
    }


def detect_k(df, max_k=10):
    detected = 0

    for rank in range(1, max_k + 1):
        cols = get_columns(rank)

        if cols["nist_mapping"] in df.columns:
            detected = rank

    return detected


def explanation_missing(row, cols):
    return (
        is_blank(row.get(cols["commonality"], ""))
        or is_blank(row.get(cols["justification"], ""))
        or is_blank(row.get(cols["differences"], ""))
    )


# ============================================================
# PROMPT
# ============================================================

def build_prompt(
    ecc_id,
    ecc_text,
    nist_id,
    nist_text,
    dense,
    sparse,
    hybrid,
    ontology,
    final_score,
    confidence
):
    synonym_text = format_synonym_groups_for_prompt()

    # Clean again before sending to GROQ.
    ecc_text = clean_control_text(ecc_text)
    nist_text = clean_control_text(nist_text)

    return f"""
You are a cybersecurity control mapping analyst.

Compare the ECC control with the mapped NIST CSF control.

When comparing the controls, treat the following terms as equivalent or closely related only where the context supports it:

{synonym_text}

ECC Control ID:
{ecc_id}

ECC Control Text:
{ecc_text}

NIST Control ID:
{nist_id}

NIST Control Text:
{nist_text}

Mapping Scores:
Dense Score: {dense}
Sparse Score: {sparse}
Hybrid Score: {hybrid}
Ontology Score: {ontology}
Final Score: {final_score}
Confidence Match: {confidence}

Return ONLY valid JSON in this exact format:

{{
  "Commonality": "...",
  "Justification": "...",
  "Differences": "..."
}}

Commonality:
Explain what the ECC control and the mapped NIST control have in common. Focus on the shared cybersecurity objective, shared topic, shared governance requirement, shared security requirement, or synonym-based conceptual overlap.

Justification:
Explain why this NIST control is a suitable mapping for the ECC control. Use the control wording, synonym relationships, and the mapping score context to support the explanation.

Differences:
Explain what is different between the ECC control and the NIST control. Mention if one control is broader, more specific, more technical, more governance-focused, or covers something not clearly stated in the other.

Rules:
- Return only valid JSON.
- Do not use markdown.
- Do not use bullet points.
- Do not use numbering.
- Do not invent requirements.
- Do not force a match only because a synonym exists.
- Use the synonym groups only when the control context supports it.
- Each field must be 2 to 4 complete sentences.
- Write in a professional audit and academic style.
"""


# ============================================================
# JSON PARSER
# ============================================================

def parse_groq_json(text):
    text = str(text).strip()
    text = fix_text_encoding(text)

    try:
        data = json.loads(text)

        return {
            "Commonality": clean_control_text(str(data.get("Commonality", "")).strip()),
            "Justification": clean_control_text(str(data.get("Justification", "")).strip()),
            "Differences": clean_control_text(str(data.get("Differences", "")).strip()),
        }

    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        try:
            data = json.loads(match.group(0))

            return {
                "Commonality": clean_control_text(str(data.get("Commonality", "")).strip()),
                "Justification": clean_control_text(str(data.get("Justification", "")).strip()),
                "Differences": clean_control_text(str(data.get("Differences", "")).strip()),
            }

        except Exception:
            pass

    return {
        "Commonality": "",
        "Justification": "",
        "Differences": ""
    }


# ============================================================
# GROQ GENERATION
# ============================================================

def generate_explanation(client, model, prompt, retries=5):
    for attempt in range(1, retries + 1):

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cybersecurity control mapping analyst. "
                            "Return only valid JSON with exactly these keys: "
                            "Commonality, Justification, Differences."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=900,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            parsed = parse_groq_json(content)

            if (
                not is_blank(parsed["Commonality"])
                and not is_blank(parsed["Justification"])
                and not is_blank(parsed["Differences"])
            ):
                return parsed

            print("Empty or incomplete GROQ response:")
            print(content)

        except Exception as e:
            print(f"GROQ error attempt {attempt}: {e}")

        wait_time = 8 * attempt
        print(f"Waiting {wait_time} seconds before retrying...")
        time.sleep(wait_time)

    return {
        "Commonality": "Explanation was not generated due to an API or parsing issue.",
        "Justification": "Explanation was not generated due to an API or parsing issue.",
        "Differences": "Explanation was not generated due to an API or parsing issue."
    }


# ============================================================
# COLUMN REORDERING
# ============================================================

def reorder_columns(df, k):
    ordered_columns = []

    base_columns = [
        "ECC id control",
        "Source Text"
    ]

    for col in base_columns:
        if col in df.columns:
            ordered_columns.append(col)

    for rank in range(1, k + 1):
        cols = get_columns(rank)

        mapping_group = [
            cols["nist_mapping"],
            cols["nist_text"],
            cols["dense"],
            cols["sparse"],
            cols["hybrid"],
            cols["ontology"],
            cols["final"],
            cols["confidence"],
            cols["commonality"],
            cols["justification"],
            cols["differences"],
        ]

        for col in mapping_group:
            if col in df.columns and col not in ordered_columns:
                ordered_columns.append(col)

    remaining_columns = [
        col for col in df.columns
        if col not in ordered_columns
    ]

    ordered_columns.extend(remaining_columns)

    return df[ordered_columns]


# ============================================================
# MAIN FULL PIPELINE
# ============================================================

def run_complete_explanation_file(
    input_path,
    output_path,
    model="llama-3.3-70b-versatile",
    max_k=10,
    save_every=3,
    max_repair_rounds=3
):
    logger = setup_logger()

    logger.info("=" * 80)
    logger.info("GENERATING COMPLETE EXPLANATION FILE WITH TEXT CLEANUP")
    logger.info("=" * 80)

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    client = setup_groq_client()

    # Read with Excel-friendly UTF-8.
    df = pd.read_csv(input_path, encoding="utf-8-sig")

    # Clean all text before processing.
    df = clean_dataframe_text_columns(df)

    logger.info(f"Original rows: {len(df)}")

    df = remove_parent_controls(df)

    logger.info(f"Rows after removing parent controls: {len(df)}")

    k = detect_k(df, max_k=max_k)

    if k == 0:
        raise ValueError("No NIST mapping columns were found.")

    logger.info(f"Detected {k} mapping groups.")

    # Create explanation columns if missing.
    for rank in range(1, k + 1):
        cols = get_columns(rank)

        for col in [
            cols["commonality"],
            cols["justification"],
            cols["differences"]
        ]:
            if col not in df.columns:
                df[col] = ""

    df = df.reset_index(drop=True)

    total_generated = 0

    # ------------------------------------------------------------
    # Initial generation + automatic repair rounds
    # ------------------------------------------------------------

    for repair_round in range(1, max_repair_rounds + 1):

        logger.info("=" * 80)
        logger.info(f"GENERATION / REPAIR ROUND {repair_round}")
        logger.info("=" * 80)

        missing_this_round = 0

        for row_index in tqdm(range(len(df)), desc=f"Round {repair_round}"):

            ecc_id = clean_control_text(df.at[row_index, "ECC id control"])
            ecc_text = clean_control_text(df.at[row_index, "Source Text"])

            for rank in range(1, k + 1):

                cols = get_columns(rank)

                if cols["nist_mapping"] not in df.columns:
                    continue

                if cols["nist_text"] not in df.columns:
                    continue

                row = df.iloc[row_index]

                nist_id = clean_control_text(row.get(cols["nist_mapping"], ""))
                nist_text = clean_control_text(row.get(cols["nist_text"], ""))

                if is_blank(nist_id):
                    continue

                if pd.isna(nist_text):
                    nist_text = ""

                # Only generate if missing.
                if not explanation_missing(row, cols):
                    continue

                missing_this_round += 1

                prompt = build_prompt(
                    ecc_id=ecc_id,
                    ecc_text=ecc_text,
                    nist_id=nist_id,
                    nist_text=nist_text,
                    dense=row.get(cols["dense"], ""),
                    sparse=row.get(cols["sparse"], ""),
                    hybrid=row.get(cols["hybrid"], ""),
                    ontology=row.get(cols["ontology"], ""),
                    final_score=row.get(cols["final"], ""),
                    confidence=row.get(cols["confidence"], "")
                )

                explanation = generate_explanation(
                    client=client,
                    model=model,
                    prompt=prompt,
                    retries=5
                )

                df.at[row_index, cols["commonality"]] = clean_control_text(explanation["Commonality"])
                df.at[row_index, cols["justification"]] = clean_control_text(explanation["Justification"])
                df.at[row_index, cols["differences"]] = clean_control_text(explanation["Differences"])

                total_generated += 1

                time.sleep(2)

                if total_generated % save_every == 0:
                    temp_df = reorder_columns(df, k)
                    temp_df = clean_dataframe_text_columns(temp_df)
                    temp_df.to_csv(output_path, index=False, encoding="utf-8-sig")
                    logger.info(f"Saved progress. Total generated so far: {total_generated}")

        df = reorder_columns(df, k)
        df = clean_dataframe_text_columns(df)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        logger.info(f"Round {repair_round} completed.")
        logger.info(f"Missing explanations found in this round: {missing_this_round}")

        if missing_this_round == 0:
            logger.info("No missing explanations remain.")
            break

    # ------------------------------------------------------------
    # Final missing count check
    # ------------------------------------------------------------

    final_missing = 0

    for row_index in range(len(df)):
        row = df.iloc[row_index]

        for rank in range(1, k + 1):
            cols = get_columns(rank)

            if cols["nist_mapping"] not in df.columns:
                continue

            if is_blank(row.get(cols["nist_mapping"], "")):
                continue

            if explanation_missing(row, cols):
                final_missing += 1

    df = reorder_columns(df, k)
    df = clean_dataframe_text_columns(df)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    logger.info("=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Final output saved to: {output_path}")
    logger.info(f"Total explanations generated or repaired: {total_generated}")
    logger.info(f"Remaining missing explanations: {final_missing}")

    if final_missing > 0:
        logger.warning(
            "Some explanations are still missing because GROQ may have failed or rate-limited. "
            "Run the same script again if needed."
        )


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    INPUT_FILE = "data/final_owl_ontology_refined_mappings.csv"

    OUTPUT_FILE = "data/final_with_explanations_COMPLETE.csv"

    run_complete_explanation_file(
        input_path=INPUT_FILE,
        output_path=OUTPUT_FILE,
        model="llama-3.3-70b-versatile",
        max_k=10,
        save_every=3,
        max_repair_rounds=3
    )