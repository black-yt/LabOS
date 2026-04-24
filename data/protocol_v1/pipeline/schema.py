"""Unified protocol schema."""
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Reagent:
    name: str
    vendor: str = ""
    catalog_id: str = ""
    rrid: str = ""
    category: str = ""  # e.g. "Antibodies", "Chemicals"


@dataclass
class Equipment:
    name: str
    vendor: str = ""
    model: str = ""


@dataclass
class Step:
    step_no: str       # "1", "1a", "2.3"
    text: str
    section: str = ""  # parent section title
    duration: str = ""


@dataclass
class Troubleshoot:
    problem: str
    solution: str


@dataclass
class Protocol:
    id: str                       # source:pmcid or source:doi
    source: str                   # star | bioprot | nprot | pio
    title: str
    doi: str = ""
    pmcid: str = ""
    pmid: str = ""
    license: str = ""
    journal: str = ""
    pub_year: str = ""
    authors: list = field(default_factory=list)
    abstract: str = ""
    domain_tags: list = field(default_factory=list)
    reagents: list = field(default_factory=list)    # list[Reagent]
    equipment: list = field(default_factory=list)   # list[Equipment]
    materials_raw: str = ""                          # unparsed prose fallback
    steps: list = field(default_factory=list)       # list[Step]
    troubleshooting: list = field(default_factory=list)
    timing: str = ""
    safety: str = ""
    references_count: int = 0
    fetched_at: str = ""
    parser_version: str = ""

    # QC fields (filled by validator)
    qc_pass: bool = False
    qc_score: float = 0.0
    qc_flags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def validate(p: Protocol, min_reagents=3, min_steps=3, min_materials_chars=150) -> None:
    """Mutates p.qc_*. Gate: reagents + equipment/materials + steps."""
    flags = []
    has_reagents = len(p.reagents) >= min_reagents
    has_equipment = len(p.equipment) >= 1 or len(p.materials_raw) >= min_materials_chars
    has_steps = len(p.steps) >= min_steps

    if not has_reagents: flags.append(f"reagents<{min_reagents}")
    if not has_equipment: flags.append("no_equipment_or_materials")
    if not has_steps: flags.append(f"steps<{min_steps}")
    if not p.title: flags.append("no_title")
    if not p.doi and not p.pmcid: flags.append("no_id")

    # score: weighted completeness
    score = 0.0
    score += min(len(p.reagents) / 10, 1.0) * 0.3
    score += (1.0 if len(p.equipment) >= 3 else len(p.equipment) / 3) * 0.2
    score += min(len(p.steps) / 20, 1.0) * 0.3
    score += (0.1 if p.troubleshooting else 0)
    score += (0.05 if p.timing else 0)
    score += (0.05 if p.abstract else 0)

    p.qc_flags = flags
    p.qc_score = round(score, 3)
    p.qc_pass = has_reagents and has_equipment and has_steps and bool(p.title)
