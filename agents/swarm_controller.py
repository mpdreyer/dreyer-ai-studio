"""
SwarmController — business logic för Ruflo Testsvärm.
Separerar orchestration från UI-rendering.
"""

from __future__ import annotations

import re
import shlex
from typing import ClassVar

from pydantic import BaseModel, field_validator, model_validator

from db.swarm_repository import SwarmRepository, SwarmRun

VALID_DOMAINS: frozenset[str] = frozenset({"general", "ai", "code"})
_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class ValidationError(ValueError):
    """Applikationsspecifikt valideringsfel (mappar från Pydantic)."""
    pass


class SwarmConfig(BaseModel):
    """Validerad svärm-konfiguration. Skapa via SwarmConfig.validate()."""

    variant: str
    variant_id: str
    n_workers: int
    max_concurrent: int
    domain: str

    # Pydantic-klass-konfiguration
    model_config: ClassVar = {"frozen": True}

    # ── Fältvalidatorer ────────────────────────────────────────────────────────

    @field_validator("variant")
    @classmethod
    def variant_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Prompt-varianten får inte vara tom.")
        if "{input}" not in v:
            raise ValueError("Prompt-varianten måste innehålla {input}-placeholder.")
        return v

    @field_validator("variant_id")
    @classmethod
    def variant_id_safe(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Variant-ID får inte vara tomt.")
        if not _SAFE_ID_RE.match(v):
            raise ValueError(
                "Variant-ID får bara innehålla bokstäver, siffror, bindestreck och understreck."
            )
        return v

    @field_validator("n_workers")
    @classmethod
    def workers_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Antal workers måste vara minst 1.")
        return v

    @field_validator("max_concurrent")
    @classmethod
    def concurrent_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Max parallella måste vara minst 1.")
        return v

    @field_validator("domain")
    @classmethod
    def domain_known(cls, v: str) -> str:
        if v not in VALID_DOMAINS:
            raise ValueError(f"Okänd domän '{v}'. Giltiga: {', '.join(sorted(VALID_DOMAINS))}")
        return v

    @model_validator(mode="after")
    def concurrent_le_workers(self) -> "SwarmConfig":
        if self.max_concurrent > self.n_workers:
            raise ValueError("Max parallella kan inte överstiga antal workers.")
        return self

    # ── Fabriksmetod med applikationsvänliga felmeddelanden ────────────────────

    @classmethod
    def validate(
        cls,
        variant: str,
        variant_id: str,
        n_workers: int,
        max_concurrent: int,
        domain: str,
    ) -> "SwarmConfig":
        """Skapar en SwarmConfig. Kastar ValidationError (ej Pydantic) vid fel."""
        from pydantic import ValidationError as PydanticError
        try:
            return cls(
                variant=variant,
                variant_id=variant_id,
                n_workers=n_workers,
                max_concurrent=max_concurrent,
                domain=domain,
            )
        except PydanticError as e:
            # Plocka ut första felmeddelandet i ett läsbart format
            first = e.errors()[0]
            raise ValidationError(first["msg"].removeprefix("Value error, ")) from e

    # ── CLI-hjälpare ───────────────────────────────────────────────────────────

    def to_cli_args(self) -> str:
        """
        Returnerar shell-säkra CLI-argument (shlex.quote på alla strängar).
        variant trunkeras för visning — kör aldrig detta som eval/shell=True.
        """
        short_variant = self.variant[:60] + ("..." if len(self.variant) > 60 else "")
        return (
            f"--variant {shlex.quote(short_variant)} "
            f"--variant-id {shlex.quote(self.variant_id)} "
            f"--workers {self.n_workers} "
            f"--concurrent {self.max_concurrent} "
            f"--domain {shlex.quote(self.domain)}"
        )


class SwarmController:
    def __init__(self, repo: SwarmRepository):
        self._repo = repo

    def get_runs(self, limit: int = 10) -> list[SwarmRun]:
        return self._repo.get_runs(limit=limit)

    def build_config(
        self,
        variant: str,
        variant_id: str,
        n_workers: int,
        max_concurrent: int,
        domain: str,
    ) -> SwarmConfig:
        """Validerar och returnerar en SwarmConfig. Kastar ValidationError vid fel."""
        return SwarmConfig.validate(variant, variant_id, n_workers, max_concurrent, domain)
