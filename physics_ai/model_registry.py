"""Model registry helpers for versioned artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import json
import time
import hashlib


@dataclass
class RegistryEntry:
    run_id: str
    base_dir: Path

    @property
    def run_dir(self) -> Path:
        return self.base_dir / self.run_id

    @property
    def artifacts_dir(self) -> Path:
        return self.run_dir / "artifacts"

    @property
    def configs_dir(self) -> Path:
        return self.run_dir / "configs"

    def ensure_dirs(self) -> None:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.configs_dir.mkdir(parents=True, exist_ok=True)


def create_registry_entry(base_dir: str = "models") -> RegistryEntry:
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_id = f"run-{timestamp}"
    entry = RegistryEntry(run_id=run_id, base_dir=Path(base_dir))
    entry.ensure_dirs()
    return entry


def save_metadata(entry: RegistryEntry, metadata: Dict[str, Any]) -> Path:
    path = entry.run_dir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def save_config(entry: RegistryEntry, config: Dict[str, Any]) -> Path:
    path = entry.configs_dir / "train_config.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_provenance(entry: RegistryEntry, artifacts: Dict[str, Path]) -> Path:
    payload = {
        "artifacts": {name: str(path) for name, path in artifacts.items()},
        "checksums": {name: sha256_file(path) for name, path in artifacts.items() if path.exists()},
    }
    path = entry.run_dir / "provenance.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
