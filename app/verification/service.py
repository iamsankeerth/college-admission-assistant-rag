from __future__ import annotations

import re

from app.models import ClaimCheck, VerificationReport


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall(text.lower()))


class FinalAnswerVerifier:
    """Final-answer verifier that delegates to NLI-based or heuristic verification.

    Uses NLIVerifier when GEMINI_API_KEY is available and NLI_VERIFIER_ENABLED is true,
    otherwise falls back to heuristic lexical overlap checking.
    """

    def __init__(self) -> None:
        from app.config import settings

        self.use_nli = getattr(settings, "nli_verifier_enabled", False)
        if self.use_nli:
            from app.verification.nli_verifier import NLIVerifier

            self._nli_verifier = NLIVerifier()
        else:
            self._nli_verifier = None

    def verify(self, answer_text: str, evidence_texts: list[str]) -> VerificationReport:
        if self._nli_verifier is not None:
            return self._nli_verifier.verify(answer_text, evidence_texts)
        return self._heuristic_verify(answer_text, evidence_texts)

    def _heuristic_verify(
        self, answer_text: str, evidence_texts: list[str]
    ) -> VerificationReport:
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
            verification_note=(
                "Heuristic claim-support verification using lexical overlap. "
                "Set NLI_VERIFIER_ENABLED=true and configure GEMINI_API_KEY for NLI-based verification."
            ),
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
