from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    INFERENCE = "inference"
    SPECULATION = "speculation"
    QUESTION = "question"


class Personality(str, Enum):
    WITNESS = "witness"
    ARCHIVIST = "archivist"
    PHANTOM = "phantom"
    ECHO = "echo"


class InvestigationCreate(BaseModel):
    title: str = "Untitled Investigation"
    description: str | None = None
    active_personality: Personality = Personality.PHANTOM
    load_sample: bool = False
    sample_id: str | None = "the_last_process"


class InvestigationOut(BaseModel):
    id: str
    title: str
    description: str | None
    created_at: str
    updated_at: str
    status: str
    active_personality: str
    configuration: dict[str, Any]
    artifact_count: int = 0
    clue_count: int = 0
    unresolved_questions: int = 0


class ArtifactOut(BaseModel):
    id: str
    investigation_id: str
    filename: str
    content_type: str
    content: str
    imported_at: str
    summary: str | None
    metadata: dict[str, Any]
    tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)


class ClueOut(BaseModel):
    id: str
    investigation_id: str
    artifact_id: str | None
    title: str
    description: str
    evidence_type: str
    confidence: float
    source_references: list[str]


class EntityOut(BaseModel):
    id: str
    investigation_id: str
    name: str
    entity_type: str
    description: str | None


class RelationshipOut(BaseModel):
    id: str
    investigation_id: str
    source_id: str
    target_id: str
    relationship_type: str
    explanation: str | None
    evidence_references: list[str]
    confidence: float
    is_manual: bool = False


class TimelineEventOut(BaseModel):
    id: str
    investigation_id: str
    description: str
    timestamp: str | None
    timestamp_precision: str
    evidence_type: str
    source_references: list[str]
    importance: str
    contradictions: list[str]


class GraphNode(BaseModel):
    id: str
    type: Literal["artifact", "clue", "entity", "event"]
    label: str
    evidence_type: str | None = None
    confidence: float | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    evidence_type: str
    confidence: float
    explanation: str | None = None


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ChatRequest(BaseModel):
    message: str
    command: str | None = None


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    source_references: list[str] = Field(default_factory=list)
    provider: str
    is_demonstration: bool = False


class ScanResult(BaseModel):
    artifacts_processed: int
    clues_created: int
    entities_created: int
    relationships_created: int
    timeline_events_created: int
    provider: str
    is_demonstration: bool = False


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    available: bool
    description: str
    approximate_size: str | None = None
    ram_hint: str | None = None


class ModelSettingsUpdate(BaseModel):
    provider: Literal["mock", "ollama"] = "mock"
    chat_model: str | None = None
    embed_model: str | None = None
    ollama_base_url: str | None = None
    semantic_search_enabled: bool | None = None


class HealthOut(BaseModel):
    status: str
    offline_capable: bool
    model_provider: str
    model_available: bool
    database: str


class ReconstructOut(BaseModel):
    case_summary: str
    established_evidence: list[str]
    connected_clues: list[str]
    unresolved_questions: list[str]
    competing_theories: list[str]
    final_story: str
    evidence_references: dict[str, list[str]]
    disclaimer: str
    provider: str
    is_demonstration: bool = False


class ExportFormat(str, Enum):
    markdown = "markdown"
    json = "json"


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    explanation: str | None = None


class InvestigationSettingsUpdate(BaseModel):
    active_personality: Personality | None = None
    custom_personality: str | None = None
