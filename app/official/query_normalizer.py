from __future__ import annotations

import re
from difflib import SequenceMatcher


TYPO_THRESHOLD = 0.85


BRANCH_ALIASES: dict[str, list[str]] = {
    "computer science and engineering": ["cse", "computer science", "cs", "cs engineering"],
    "electrical engineering": ["ee", "electrical", "electricals"],
    "electronics and communication engineering": ["ece", "electronics", "e and c", "ec"],
    "mechanical engineering": ["me", "mech", "mechanical"],
    "civil engineering": ["ce", "civil"],
    "chemical engineering": ["ch", "chem", "chemical"],
    "metallurgical engineering": ["mme", "metallurgy", "mme"],
    "materials science and engineering": ["mse", "materials"],
    "biotechnology": ["biotech", "bio tech"],
    "information technology": ["it", "it engineering"],
    "instrumentation engineering": ["inst", "instrumentation"],
    "computer science": ["cs", "computer science"],
    "electronics engineering": ["ee", "electronics"],
    "production engineering": ["pe", "production"],
    "aerospace engineering": ["ae", "aerospace", "astro"],
    "architecture": ["arch", "b.arch", "b.arch"],
    "mathematics and computing": ["mnc", "math and comp", "mathematics"],
    "engineering physics": ["ep", "eng physics"],
    "data science": ["ds", "data science", "data analytics"],
    "artificial intelligence": ["ai", "artificial intelligence", "ml"],
    "computer science and technology": ["cst", "computer science"],
    "electrical and electronics engineering": ["eee", "electrical and electronics"],
    " electronics and telecommunication engineering": ["etc", "electronics and telecommunication"],
    "metallurgy and materials engineering": ["mme", "metallurgy", "materials"],
    "textile engineering": ["tx", "textile"],
    "environmental engineering": ["env", "environmental"],
    "water resources engineering": ["wr", "water resources", "hydrology"],
    "ocean engineering": ["oe", "ocean"],
    "mineral engineering": ["mine", "mineral"],
    "mining engineering": ["mining", "mine"],
}


COLLEGE_NORMALIZATIONS: dict[str, list[str]] = {
    "IIT Bombay": ["iit bombay", "iit b", "indian institute of technology bombay", "iitb"],
    "IIT Delhi": ["iit delhi", "iit d", "indian institute of technology delhi", "iitd"],
    "IIT Madras": ["iit madras", "iit m", "indian institute of technology madras", "iitm"],
    "IIT Kanpur": ["iit kanpur", "iit k", "indian institute of technology kanpur", "iitk"],
    "IIT Kharagpur": ["iit kharagpur", "iit kgp", "indian institute of technology kharagpur"],
    "IIT Roorkee": ["iit roorkee", "iit r", "indian institute of technology roorkee", "iitroorkee"],
    "IIT Guwahati": ["iit guwahati", "iit g", "indian institute of technology guwahati"],
    "IIT Hyderabad": ["iit hyderabad", "iith", "indian institute of technology hyderabad"],
    "IIT (BHU) Varanasi": ["iit bhu", "iit varanasi", "bhu", "banaras hindu university"],
    "NIT Trichy": ["nit trichy", "nit tiruchirappalli", "nit trichy", "national institute of technology trichy"],
    "NIT Warangal": ["nit warangal", "nit w", "national institute of technology warangal"],
    "BITS Pilani": ["bits pilani", "bits", "birla institute pilani", "bits pilani campus"],
    "IIIT Hyderabad": ["iiit hyderabad", "iiit h", "international institute of information technology hyderabad"],
    "VIT Vellore": ["vit vellore", "vit", "vellore institute of technology"],
    "Anna University": ["anna university", "anna univ", "ceg", "act"],
}


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "if", "in", "is", "it", "its", "of", "on", "or", "that", "the",
    "to", "was", "what", "when", "where", "which", "who", "will",
}


def normalize_branch(branch: str) -> str:
    normalized = branch.lower().strip()
    for canonical, aliases in BRANCH_ALIASES.items():
        if normalized in aliases or normalized == canonical.lower():
            return canonical
    return branch.strip()


def normalize_college_name(name: str) -> str | None:
    normalized = name.lower().strip()
    for canonical, aliases in COLLEGE_NORMALIZATIONS.items():
        if normalized in aliases or normalized == canonical.lower():
            return canonical
    return None


def _similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= TYPO_THRESHOLD


def _fix_typos(token: str, candidates: set[str]) -> str:
    for candidate in candidates:
        if _similar(token, candidate):
            return candidate
    return token


def expand_query(query: str) -> str:
    query_lower = query.lower()
    expanded_terms: list[str] = []

    for college_canonical, aliases in COLLEGE_NORMALIZATIONS.items():
        for alias in aliases:
            if alias in query_lower and college_canonical.lower() not in query_lower:
                expanded_terms.append(college_canonical)
                break

    for branch_canonical, aliases in BRANCH_ALIASES.items():
        for alias in aliases:
            if alias in query_lower and branch_canonical.lower() not in query_lower:
                expanded_terms.append(branch_canonical)
                break

    if expanded_terms:
        query = query + " " + " ".join(expanded_terms)

    return query


def normalize_query(query: str) -> str:
    query = query.strip()
    query = re.sub(r"\s+", " ", query)
    query = query.replace("\n", " ").replace("\t", " ")
    query = re.sub(r"[^\w\s\-.,!?()]", "", query)
    return query.strip()


def extract_query_terms(query: str) -> list[str]:
    normalized = normalize_query(query)
    tokens = re.findall(r"[\w]+", normalized.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def normalize_for_cache(query: str, college_name: str | None = None) -> str:
    key = normalize_query(query.lower())
    if college_name:
        normalized_college = normalize_college_name(college_name)
        if normalized_college:
            key = key.replace(college_name.lower(), normalized_college.lower())
    return key
