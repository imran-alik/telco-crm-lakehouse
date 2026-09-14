from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def repo_root() -> Path:
    return _repo_root()


@dataclass(frozen=True)
class SamplePaths:
    samples_dir: Path = field(default_factory=lambda: _repo_root() / "data" / "source" / "samples")

    @property
    def customers_crm(self) -> Path:
        return self.samples_dir / "customers_crm.csv"

    @property
    def agents(self) -> Path:
        return self.samples_dir / "agents.csv"

    @property
    def calls(self) -> Path:
        return self.samples_dir / "calls.csv"

    @property
    def offers_disposition(self) -> Path:
        return self.samples_dir / "offers_disposition.csv"

    @property
    def intent_labels(self) -> Path:
        return self.samples_dir / "intent_labels.csv"

    @property
    def demographics(self) -> Path:
        return self.samples_dir / "demographics.csv"


@dataclass(frozen=True)
class SampleGenerationConfig:
    seed: int = 42
    customers_count: int = 300
    agents_count: int = 40
    calls_count: int = 1500
    offers_count: int = 800
    intent_labels_count: int = 1500
    demographics_count: int = 300
    paths: SamplePaths = field(default_factory=SamplePaths)

    def ensure_dirs(self) -> None:
        self.paths.samples_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class LakehouseConfig:
    db_path: str = field(
        default_factory=lambda: str(_repo_root() / "data" / "sink" / "lakehouse.db")
    )
    samples_dir: str = field(
        default_factory=lambda: str(_repo_root() / "data" / "source" / "samples")
    )
    dlq_dir: str = field(
        default_factory=lambda: str(_repo_root() / "data" / "sink" / "quarantine_dlq")
    )
    bronze_prefix: str = "bronze_"
    silver_prefix: str = "silver_"
    gold_prefix: str = "gold_"
    mart_prefix: str = "mart_"
    duckdb_batch_size: int = 200

    def ensure_dirs(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.dlq_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def for_tests(cls, tmp_path: Path, *, samples_dir: str | None = None) -> LakehouseConfig:
        return cls(
            db_path=str(tmp_path / "lakehouse.db"),
            samples_dir=samples_dir or str(tmp_path / "samples"),
            dlq_dir=str(tmp_path / "quarantine_dlq"),
        )
