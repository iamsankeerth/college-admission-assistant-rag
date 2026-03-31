from __future__ import annotations

import re
from typing import Any

from app.models import ClaimCheck, VerificationReport


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


class HeuristicVerifier:
    def verify(self, answer_text: str, evidence_texts: list[str]) -> VerificationReport:
        claims = self._extract_claims(answer_text)
        checks: list[ClaimCheck] = []
        for claim in claims:
            checks.append(self._check_claim(claim, evidence_texts))

        supported_count = sum(1 for check in checks if check.supported)
        unsupported_count = len(checks) - supported_count
        return VerificationReport(
            checks=checks,
            supported_count=supported_count,
            unsupported_count=unsupported_count,
            verification_note="Heuristic claim-support verification using lexical overlap.",
        )

    def _extract_claims(self, answer_text: str) -> list[str]:
        claims: list[str] = []
        for line in answer_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.endswith(":") or stripped.endswith("]"):
                continue
            if stripped in {
                "Official Recommendation",
                "Official Sources",
                "Student Signals: Reddit",
                "Student Signals: YouTube",
                "Cautions and Bias Warnings",
                "Bottom Line",
            }:
                continue
            if stripped.startswith("- "):
                claims.append(stripped[2:])
            elif "." in stripped and len(stripped.split()) >= 6:
                claims.append(stripped)
        return claims

    def _check_claim(self, claim: str, evidence_texts: list[str]) -> ClaimCheck:
        claim_tokens = _tokens(claim)
        best_score = 0.0
        best_evidence: list[str] = []
        for evidence in evidence_texts:
            evidence_tokens = _tokens(evidence)
            if not claim_tokens or not evidence_tokens:
                continue
            overlap = claim_tokens & evidence_tokens
            score = len(overlap) / max(len(claim_tokens), 1)
            if score > best_score:
                best_score = score
                best_evidence = [evidence]
        return ClaimCheck(
            claim=claim,
            supported=best_score >= 0.35,
            confidence_score=round(best_score, 3),
            evidence=best_evidence,
        )


class NLIVerifier:
    """NLI-based verifier using Gemini for entailment detection.

    Replaces the heuristic overlap checker with a proper natural language
    inference model. Falls back to heuristic verification if NLI fails.
    """

    def __init__(self) -> None:
        from app.config import settings
        self.gemini_api_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model

    def _build_nli_prompt(self, claim: str, evidence_texts: list[str]) -> str:
        combined_evidence = "\n\n".join(f"- {ev}" for ev in evidence_texts[:5])
        return (
            f"You are a strict factual verification assistant.\n\n"
            f"Claim to verify:\n\"{claim}\"\n\n"
            f"Evidence (from official documents):\n{combined_evidence}\n\n"
            f"Task: Determine if the claim is SUPPORTED, REFUTED, or NOT VERIFIABLE "
            f"based solely on the evidence above.\n\n"
            f"Rules:\n"
            f"- SUPPORTED: The claim is directly confirmed by the evidence\n"
            f"- REFUTED: The evidence directly contradicts the claim\n"
            f"- NOT VERIFIABLE: The evidence does not contain enough information to verify the claim\n\n"
            f"Response format (JSON only, no other text):\n"
            f'{{"verdict": "SUPPORTED|REFUTED|NOT_VERIFIABLE", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}\n'
        )

    def _call_nli(self, claim: str, evidence_texts: list[str]) -> dict[str, Any] | None:
        if not self.gemini_api_key or not evidence_texts:
            return None

        try:
            from google import genai

            client = genai.Client(api_key=self.gemini_api_key)
            prompt = self._build_nli_prompt(claim, evidence_texts)

            response = client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
            )
            response_text = response.text.strip()

            json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group(0))
        except Exception:
            pass
        return None

    def verify(self, answer_text: str, evidence_texts: list[str]) -> VerificationReport:
        claims = self._extract_claims(answer_text)
        checks: list[ClaimCheck] = []

        for claim in claims:
            nli_result = self._call_nli(claim, evidence_texts)

            if nli_result is not None:
                verdict = nli_result.get("verdict", "NOT_VERIFIABLE")
                confidence = float(nli_result.get("confidence", 0.5))
                supported = verdict == "SUPPORTED"
            else:
                supported, confidence = self._heuristic_check(claim, evidence_texts)

            checks.append(
                ClaimCheck(
                    claim=claim,
                    supported=supported,
                    confidence_score=round(confidence, 3),
                    evidence=[],
                )
            )

        supported_count = sum(1 for check in checks if check.supported)
        unsupported_count = len(checks) - supported_count
        return VerificationReport(
            checks=checks,
            supported_count=supported_count,
            unsupported_count=unsupported_count,
            verification_note=(
                "NLI-based verification using Gemini. "
                "Falls back to heuristic overlap scoring when NLI is unavailable."
            ),
        )

    def _heuristic_check(self, claim: str, evidence_texts: list[str]) -> tuple[bool, float]:
        claim_tokens = _tokens(claim)
        best_score = 0.0
        for evidence in evidence_texts:
            evidence_tokens = _tokens(evidence)
            if not claim_tokens or not evidence_tokens:
                continue
            overlap = claim_tokens & evidence_tokens
            score = len(overlap) / max(len(claim_tokens), 1)
            best_score = max(best_score, score)
        return best_score >= 0.35, best_score

    def _extract_claims(self, answer_text: str) -> list[str]:
        claims: list[str] = []
        for line in answer_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.endswith(":") or stripped.endswith("]"):
                continue
            if stripped in {
                "Official Recommendation",
                "Official Sources",
                "Student Signals: Reddit",
                "Student Signals: YouTube",
                "Cautions and Bias Warnings",
                "Bottom Line",
            }:
                continue
            if stripped.startswith("- "):
                claims.append(stripped[2:])
            elif "." in stripped and len(stripped.split()) >= 6:
                claims.append(stripped)
        return claims


def build_verifier(use_nli: bool = False) -> HeuristicVerifier | NLIVerifier:
    if use_nli:
        return NLIVerifier()
    return HeuristicVerifier()
