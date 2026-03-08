import csv
import json

from physics_ai.model_registry import create_registry_entry, save_config, save_metadata
from physics_ai.model_registry_cli import (
    archive_registry_entry,
    export_registry,
    list_registry_entries,
    restore_registry_entry,
    show_registry_entry,
    tag_registry_entry,
)


def test_registry_cli_list_and_show(tmp_path) -> None:
    entry = create_registry_entry(base_dir=str(tmp_path))
    save_metadata(entry, {"training": {"operator_vocab": 3}, "dataset": {"record_count": 5}})
    save_config(entry, {"model_type": "transformer", "model_dim": 32})

    rows = list_registry_entries(base_dir=str(tmp_path))
    assert rows
    assert rows[0]["model_type"] == "transformer"

    payload = show_registry_entry(entry.run_id, base_dir=str(tmp_path))
    assert payload["metadata"]["dataset"]["record_count"] == 5
    assert json.loads(json.dumps(payload))["config"]["model_dim"] == 32

    export_path = export_registry(str(tmp_path), (tmp_path / "registry.csv").as_posix(), fmt="csv")
    with export_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert rows and rows[0]["model_type"] == "transformer"

    tag_registry_entry(entry.run_id, ["baseline", "gpu"], base_dir=str(tmp_path))
    tagged_rows = list_registry_entries(base_dir=str(tmp_path))
    assert "gpu" in (tagged_rows[0]["tags"] or "")

    archived = archive_registry_entry(entry.run_id, base_dir=str(tmp_path))
    assert archived.exists()
    assert not (tmp_path / entry.run_id).exists()
    restored = restore_registry_entry(entry.run_id, base_dir=str(tmp_path))
    assert restored.exists()
