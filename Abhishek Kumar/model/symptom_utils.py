"""
symptom_utils.py
------------------
Shared helper functions used by BOTH the training script and the Flask
backend, so the exact same symptom vocabulary and text-matching logic is
used everywhere.

Why this file exists:
The real dataset (model/data/Training.csv) has 132 symptom columns like
"skin_rash", "high_fever", "joint_pain". Users don't type like that —
they type free text like "I have a rash and fever". This module bridges
that gap:

1. `clean_symptom_name()`      -> "skin_rash" becomes "skin rash" (for display)
2. `load_symptom_columns()`    -> reads the 132 raw column names from the CSV
3. `extract_symptoms_from_text()` -> given free text, figures out which of
   the 132 known symptoms were mentioned (simple, explainable keyword
   matching — no heavy NLP library needed, perfect for a college project)
"""

import os
import re
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(CURRENT_DIR, "data", "Training.csv")


def clean_symptom_name(raw_name: str) -> str:
    """Converts a raw column name like 'high_fever' -> 'high fever'."""
    name = raw_name.strip().lower()
    name = name.replace("_", " ")
    name = re.sub(r"\s+", " ", name)          # collapse double spaces
    name = name.replace(" .1", "")             # fixes 'fluid_overload.1' duplicate column
    name = name.strip()
    return name


def load_symptom_columns():
    """
    Reads Training.csv and returns:
        raw_columns   -> original column names, e.g. 'skin_rash' (used as model features)
        display_names -> cleaned, human-readable names, e.g. 'skin rash'
    Both lists are in the same order and same length (132 items).
    """
    df = pd.read_csv(DATASET_PATH, nrows=1)
    raw_columns = [c.strip() for c in df.columns if c.strip().lower() != "prognosis"]
    display_names = [clean_symptom_name(c) for c in raw_columns]
    return raw_columns, display_names


def extract_symptoms_from_text(text: str, raw_columns, display_names):
    """
    Given a free-text sentence (e.g. "I have chest pain and vomiting"),
    returns the list of RAW symptom column names that were mentioned.

    Matching strategy (kept intentionally simple + explainable):
      1. Exact phrase match: does the cleaned symptom phrase appear
         as a substring of the user's text?
      2. Word-overlap fallback: for multi-word symptoms, if most of the
         individual words appear somewhere in the text, count it as a match
         (handles reordering, e.g. "pain in stomach" vs "stomach pain").
    """
    text_clean = re.sub(r"[^a-z\s]", " ", text.lower())
    text_clean = re.sub(r"\s+", " ", text_clean).strip()
    text_words = set(text_clean.split())

    matched = []
    for raw, display in zip(raw_columns, display_names):
        if not display:
            continue

        # Strategy 1: direct substring match (handles most real cases)
        if display in text_clean:
            matched.append(raw)
            continue

        # Strategy 2: word-overlap match for multi-word symptoms only
        symptom_words = [w for w in display.split() if len(w) > 2]
        if len(symptom_words) >= 2:
            overlap = sum(1 for w in symptom_words if w in text_words)
            if overlap / len(symptom_words) >= 0.7:
                matched.append(raw)

    return matched
