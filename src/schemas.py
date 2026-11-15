"""Pydantic v2 data contracts for TrialSwarm AI."""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class LineCitation(BaseModel):
    """Exact verbatim source anchor into either a protocol or EHR document."""

    doc_type: Literal["PROTOCOL", "EHR"]
    doc_id: str
    line_start: int
    line_end: int
    verbatim_quote: str
    verified: bool = False


class CriterionRule(BaseModel):
    """Structured clinical eligibility criterion extracted from protocol text."""

    rule_id: str
    category: Literal["INCLUSION", "EXCLUSION"]
    title: str
    rule_type: str
    operator: str
    threshold_value: Optional[Any] = None
    unit: Optional[str] = None
    citation: LineCitation


class MedicationEntry(BaseModel):
    """Extracted patient medication, dose, schedule, and washout timing."""

    name: str
    drug_class: str
    daily_dose_mg: Optional[float] = None
    raw_dose_text: str
    start_date: Optional[str] = None
    last_dose_date: Optional[str] = None
    ongoing: bool
    citation: Optional[LineCitation] = None


class RadiationEntry(BaseModel):
    """Extracted patient radiotherapy course details."""

    site: str
    dose_gy: float
    end_date: str
    is_thoracic_lung: bool = False
    citation: Optional[LineCitation] = None


class PatientPhenotype(BaseModel):
    """Structured patient clinical phenotype grounded in EHR line citations."""

    age: Optional[int] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    stage: Optional[str] = None
    ecog: Optional[int] = None
    measurable_recist: Optional[bool] = None
    prior_metastatic_lines: int = 0
    biomarkers: dict[str, Any] = Field(
        default_factory=lambda: {
            "kras_g12c": None,
            "pd_l1_tps": None,
            "egfr_mut": None,
            "alk_fusion": None,
            "msi_high": None,
            "tmb_mut_mb": None,
            "tnbc_confirmed": None,
            "pending_panels": [],
        }
    )
    labs: dict[str, Any] = Field(
        default_factory=lambda: {
            "egfr_ml_min": None,
            "ast_u_l": None,
            "alt_u_l": None,
            "bilirubin_mg_dl": None,
            "anc_u_l": None,
            "platelets_u_l": None,
        }
    )
    medications: list[MedicationEntry] = Field(default_factory=list)
    radiation_history: list[RadiationEntry] = Field(default_factory=list)
    cns_status: dict[str, Any] = Field(default_factory=dict)
    autoimmune_active: bool = False
    prior_grade3_irae: bool = False
    live_vaccine_date: Optional[str] = None
    major_surgery_date: Optional[str] = None
    extraction_citations: list[LineCitation] = Field(default_factory=list)

    # Supplemental clinical flags supporting multi-trial rule evaluation
    able_to_swallow_oral: bool = True
    accessible_biopsy_lesion: Optional[Any] = None
    prior_malignancy_2yr: bool = False
    radiation_complication: bool = False
    histology_group: Optional[str] = None
    prior_lines_detail: list[dict[str, Any]] = Field(default_factory=list)


class SafetyFinding(BaseModel):
    """Deterministic clinical safety and pharmacology calculation result (R1-R5)."""

    rule_code: str
    severity: Literal["PASS", "BLOCKER", "NEEDS_REVIEW"]
    title: str
    calculation_detail: str
    prednisone_eq_mg: Optional[float] = None
    washout_days_elapsed: Optional[int] = None
    washout_days_required: Optional[int] = None
    earliest_rescreen_date: Optional[str] = None
    citations: list[LineCitation] = Field(default_factory=list)


class CriterionVerdict(BaseModel):
    """Criterion-level evaluation grounded in citations and compared against naive baseline."""

    rule_id: str
    criterion: str
    category: Literal["INCLUSION", "EXCLUSION"]
    status: Literal[
        "MET",
        "NOT_MET",
        "EXCLUDED",
        "NEEDS_REVIEW",
        "UNVERIFIED_CITATION_BLOCKED",
    ]
    naive_baseline_status: Optional[str] = None
    reasoning: str
    citations: list[LineCitation]
    verified_by_rule_engine: bool = True


class SwarmBoardMessage(BaseModel):
    """Single message posted on the Antigravity /swarm coordination board."""

    seq: int
    author: str
    mentions: list[str]
    role: str
    model_used: str
    summary: str
    latency_ms: int
    timestamp_iso: str


class SwarmMemberStatus(BaseModel):
    """Live or final roster status of an agent in the swarm."""

    name: str
    role: str
    model: str
    state: Literal["working", "waiting", "completed"]
    latest_seq: int


class SignOffPacket(BaseModel):
    """Human-in-the-loop clinical coordinator / PI sign-off packet."""

    packet_id: str
    action_type: Literal[
        "STAGE_ECRF_PRE_SCREEN",
        "PLACE_WASHOUT_HOLD",
        "REQUEST_REFLEX_BIOMARKERS",
    ]
    status: Literal["PENDING_HUMAN_SIGNOFF", "SIGNED_APPROVED", "SIGNED_OVERRIDE"]
    title: str
    recommendation: str
    earliest_rescreen_date: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AuditReport(BaseModel):
    """Complete verified screening audit report emitted by @coordinator."""

    run_id: str
    nct_id: str
    patient_id: str
    patient_name: str
    trial_title: str
    execution_mode: str
    overall_verdict: Literal["ELIGIBLE", "CONTRAINDICATED", "NEEDS_HUMAN_REVIEW"]
    naive_baseline_verdict: str
    caught_hidden_trap: bool
    trap_explanation: Optional[str] = None
    elapsed_seconds: float
    estimated_compute_usd: float
    citation_verification_rate: float
    unverified_claims_blocked: int
    protocol_lines: list[dict[str, Any]]
    ehr_lines: list[dict[str, Any]]
    roster: list[SwarmMemberStatus]
    board_posts: list[SwarmBoardMessage]
    safety_findings: list[SafetyFinding]
    criterion_verdicts: list[CriterionVerdict]
    signoff_packet: SignOffPacket
    evidence_pmids: list[str]


class SignOffAction(BaseModel):
    """Human sign-off submission for a staged SignOffPacket."""

    run_id: str
    packet_id: str
    decision: Literal["APPROVE", "OVERRIDE"]
    reviewer_name: str
    reviewer_role: str
    clinical_note: str = ""


class SignOffReceipt(BaseModel):
    """Tamper-evident cryptographic receipt of human clinical sign-off."""

    receipt_id: str
    run_id: str
    packet_id: str
    decision: str
    reviewer_name: str
    reviewer_role: str
    clinical_note: str
    sha256_hash: str
    signed_at_iso: str


class AdversarialTrapResult(BaseModel):
    """Result of the adversarial hallucination & naive baseline trap verification probe."""

    case_id: str
    nct_id: str
    injected_hallucination_quote: str
    verifier_status: str
    unverified_claims_blocked: int
    naive_steroid_verdict: str
    trialswarm_steroid_verdict: str
    prednisone_eq_mg: float
    earliest_rescreen_date: Optional[str] = None
    details: str
