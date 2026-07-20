from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ai_sdr_platform.src.agents.prospect_intelligence.models import (
    ProspectIntelligenceListResponse,
    ProspectIntelligenceRequest,
    ProspectIntelligenceResult,
    ProspectOutcome,
    ModelTrainingRequest,
    ModelTrainingResponse,
    RankingSystemStatus,
)
from ai_sdr_platform.src.agents.prospect_intelligence.monitoring import IntelligenceMonitor
from ai_sdr_platform.src.agents.prospect_intelligence.personalization import PersonalizationAgent
from ai_sdr_platform.src.agents.prospect_intelligence.ranking import (
    LocalRankingProvider,
    MetaRankRankingProvider,
)
from ai_sdr_platform.src.agents.prospect_intelligence.repository import (
    SQLAlchemyProspectIntelligenceRepository,
)
from ai_sdr_platform.src.agents.prospect_intelligence.predictors import (
    ArtifactProbabilityPredictor,
    HeuristicProbabilityPredictor,
)
from ai_sdr_platform.src.agents.prospect_intelligence.service import ProspectIntelligenceService
from ai_sdr_platform.src.shared.config import settings
from ai_sdr_platform.src.agents.prospect_intelligence.training import ProspectModelTrainer
from ai_sdr_platform.src.agents.prospect_intelligence.metarank_events import (
    SDRMetaRankEventStore,
)

router = APIRouter(prefix="/prospect-intelligence", tags=["prospect-intelligence"])
_repository = SQLAlchemyProspectIntelligenceRepository()
_service = ProspectIntelligenceService(repository=_repository)


def configure_prospect_intelligence_service(
    *,
    llm_router: object | None = None,
) -> ProspectIntelligenceService:
    global _service
    event_store = SDRMetaRankEventStore(settings.intelligence_metarank_event_path)
    local_ranking = LocalRankingProvider(event_store=event_store)
    ranking_provider = (
        MetaRankRankingProvider(
            base_url=settings.intelligence_metarank_url,
            model_name=settings.intelligence_metarank_model,
            fallback=local_ranking,
            event_store=event_store,
        )
        if settings.intelligence_metarank_url
        else local_ranking
    )
    _service = ProspectIntelligenceService(
        repository=_repository,
        intent_predictor=(
            ArtifactProbabilityPredictor(
                model_path=settings.intelligence_intent_model_path,
                model_name="intent_probability",
                model_version=settings.intelligence_intent_model_version,
            )
            if settings.intelligence_intent_model_path
            else HeuristicProbabilityPredictor("intent")
        ),
        reply_predictor=(
            ArtifactProbabilityPredictor(
                model_path=settings.intelligence_reply_model_path,
                model_name="reply_propensity",
                model_version=settings.intelligence_reply_model_version,
            )
            if settings.intelligence_reply_model_path
            else HeuristicProbabilityPredictor("reply")
        ),
        meeting_predictor=(
            ArtifactProbabilityPredictor(
                model_path=settings.intelligence_meeting_model_path,
                model_name="meeting_propensity",
                model_version=settings.intelligence_meeting_model_version,
            )
            if settings.intelligence_meeting_model_path
            else HeuristicProbabilityPredictor("meeting")
        ),
        qualification_predictor=(
            ArtifactProbabilityPredictor(
                model_path=settings.intelligence_qualification_model_path,
                model_name="qualification_propensity",
                model_version=settings.intelligence_qualification_model_version,
            )
            if settings.intelligence_qualification_model_path
            else HeuristicProbabilityPredictor("qualification")
        ),
        ranking_provider=ranking_provider,
        personalization_agent=PersonalizationAgent(llm_router=llm_router),
        monitor=IntelligenceMonitor(event_path=settings.intelligence_monitor_path or None),
    )
    return _service


def get_prospect_intelligence_service() -> ProspectIntelligenceService:
    return _service


def get_model_trainer() -> ProspectModelTrainer:
    return ProspectModelTrainer(
        repository=_repository,
        mlflow_tracking_uri=settings.intelligence_mlflow_tracking_uri or None,
    )


@router.post("/analyze", response_model=ProspectIntelligenceResult)
def analyze_prospect(
    payload: ProspectIntelligenceRequest,
    service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
) -> ProspectIntelligenceResult:
    try:
        return service.analyze(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prospect intelligence failed: {exc}") from exc


@router.get("", response_model=ProspectIntelligenceListResponse)
def list_intelligence(
    account_id: str | None = Query(default=None),
    service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
) -> ProspectIntelligenceListResponse:
    items = service.list_results(account_id=account_id)
    return ProspectIntelligenceListResponse(items=items, total=len(items))


@router.get("/ranking/status", response_model=RankingSystemStatus)
def ranking_status(
    service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
) -> RankingSystemStatus:
    return service.ranking_status()


@router.get("/{contact_id}", response_model=ProspectIntelligenceResult)
def get_intelligence(
    contact_id: str,
    service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
) -> ProspectIntelligenceResult:
    result = service.get_latest(contact_id)
    if not result:
        raise HTTPException(status_code=404, detail="Prospect intelligence result not found")
    return result


@router.post("/outcomes", response_model=ProspectOutcome)
def record_outcome(
    payload: ProspectOutcome,
    service: ProspectIntelligenceService = Depends(get_prospect_intelligence_service),
) -> ProspectOutcome:
    try:
        return service.record_outcome(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/models/train", response_model=ModelTrainingResponse)
def train_models(
    payload: ModelTrainingRequest,
    trainer: ProspectModelTrainer = Depends(get_model_trainer),
) -> ModelTrainingResponse:
    return trainer.train(payload)
