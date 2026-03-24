from __future__ import annotations

import re

from app.models import ClaimCheck, VerificationReport


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


class FinalAnswerVerifier:
    """Heuristic NLI-style verifier over the final evidence bundle.

    This is an optional claim-support check, not a full transformer-based entailment model.
    It checks whether final answer claims have enough lexical support in the retrieved evidence.
    """

    def verify(self, answer_text: str, evidence_texts: list[str]) -> VerificationReport:
        claims = self._extract_claims(answer_text)
        checks: list[ClaimCheck] = []
        for claim in claims:
            checks.append(self._check_claim(claim, evidence_texts))

        supported_count = sum(1 for check in checks if check.supported)
        unsupported_count = len(checks) - supported_count
        note = (
            "Final-answer verification uses a heuristic claim-support layer over retrieved evidence. "
            "It is meant to catch obvious unsupported statements and can later be replaced by a full NLI model."
        )
        return VerificationReport(
            checks=checks,
            supported_count=supported_count,
            unsupported_count=unsupported_count,
            verification_note=note,
        )

    def _extract_claims(self, answer_text: str) -> list[str]:
        claims: list[str] = []
        for line in answer_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.endswith(":"):
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
