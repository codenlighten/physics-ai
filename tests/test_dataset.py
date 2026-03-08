from physics_ai.dataset_generator import DatasetConfig, generate_dataset, build_metadata, validate_schema
from physics_ai.model_registry import create_registry_entry, write_provenance


def test_generate_dataset_records() -> None:
    records = generate_dataset(DatasetConfig(universe_count=5, seed=0))
    assert len(records) == 5
    assert "wave_speed" in records[0]
    assert "frequency" in records[0]


def test_build_metadata() -> None:
    records = generate_dataset(DatasetConfig(universe_count=3, seed=1))
    metadata = build_metadata(records, DatasetConfig(universe_count=3, seed=1))
    assert metadata["record_count"] == 3
    assert "feature_names" in metadata
    assert "schema_hash" in metadata


def test_validate_schema() -> None:
    records = generate_dataset(DatasetConfig(universe_count=2, seed=2))
    validate_schema(records, ["wave_speed", "wavelength", "frequency"])


def test_provenance_helpers(tmp_path) -> None:
    entry = create_registry_entry(base_dir=str(tmp_path))
    artifact = entry.artifacts_dir / "dummy.txt"
    artifact.write_text("data", encoding="utf-8")
    provenance = write_provenance(entry, {"dummy": artifact})
    assert provenance.exists()
