"""Exam metrics model used by view layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Examen:
    total: int
    aciertos: int
    fallos: int

    @property
    def blancos(self) -> int:
        return self.total - (self.aciertos + self.fallos)

    @property
    def netas(self) -> float:
        return self.aciertos - (self.fallos * 0.33)

    @property
    def nota_sobre_diez(self) -> float:
        if self.total <= 0:
            return 0.0
        return (max(0.0, self.netas) / self.total) * 10