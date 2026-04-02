from __future__ import annotations

from app.official.service import OfficialEvidenceService
from app.public_signals.service import PublicSignalsService
from app.verification.service import FinalAnswerVerifier
from app.recommendation import RecommendationService

official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()
recommendation_service = RecommendationService(
    official_service=official_service,
    public_signals_service=public_signals_service,
)
