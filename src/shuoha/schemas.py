from enum import Enum

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    CONSIDER = "consider"
    WAIT = "wait"
    AVOID_FOR_NOW = "avoid_for_now"


class VerdictBias(str, Enum):
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    ERROR = "error"


class EvidenceSignal(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class EvidenceItem(BaseModel):
    name: str
    signal: EvidenceSignal
    raw_value: str | float | int
    plain_text: str


class BasicContext(BaseModel):
    industry: str | None = None
    company_summary: str


class TrendSnapshot(BaseModel):
    current_price: float
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    bias_ma5: float
    support_level: float
    resistance_level: float
    volume_ratio: float
    trend_score: int
    ma_alignment: str


class RiskProfile(BaseModel):
    risk_level: str
    risk_score: int
    hard_veto: bool
    chase_risk: bool
    volatility: float
    max_drawdown: float
    reasons: list[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    no_position: str
    has_position: str
    trigger_condition: str
    invalidation_condition: str
    stop_loss: str
    watch_points: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    status: AnalysisStatus
    stock_code: str
    company_name: str
    as_of_date: str
    verdict: Verdict | None = None
    bias: VerdictBias = VerdictBias.NEUTRAL
    confidence: Confidence
    technical_evidence: list[EvidenceItem] = Field(default_factory=list)
    risk_evidence: list[EvidenceItem] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    data_warnings: list[str] = Field(default_factory=list)
    basic_context: BasicContext | None = None
    trend_snapshot: TrendSnapshot | None = None
    risk_profile: RiskProfile | None = None
    action_plan: ActionPlan | None = None
    disclaimer: str
