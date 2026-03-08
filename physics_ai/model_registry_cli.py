"""CLI helpers for inspecting model registry runs."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List


def _load_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_registry_entries(base_dir: str = "models") -> List[Dict[str, Any]]:
    root = Path(base_dir)
    if not root.exists():
        return []
    runs = sorted([path for path in root.iterdir() if path.is_dir() and path.name.startswith("run-")], reverse=True)
    rows: List[Dict[str, Any]] = []
    for run in runs:
        metadata = _load_json(run / "metadata.json") or {}
        config = _load_json(run / "configs" / "train_config.json") or {}
        tags = metadata.get("tags") if isinstance(metadata, dict) else None
        rows.append({
            "run_id": run.name,
            "path": str(run),
            "records": metadata.get("dataset", {}).get("record_count"),
            "model_type": config.get("model_type"),
            "model_dim": config.get("model_dim"),
            "operator_vocab": metadata.get("training", {}).get("operator_vocab"),
            "device": metadata.get("training", {}).get("device"),
            "tags": ",".join(tags) if tags else None,
        })
    return rows


def show_registry_entry(run_id: str, base_dir: str = "models") -> Dict[str, Any]:
    run_path = Path(base_dir) / run_id
    if not run_path.exists():
        raise FileNotFoundError(f"Registry run not found: {run_id}")
    return {
        "run_id": run_id,
        "metadata": _load_json(run_path / "metadata.json"),
        "config": _load_json(run_path / "configs" / "train_config.json"),
        "provenance": _load_json(run_path / "provenance.json"),
    }


def export_registry(base_dir: str, output_path: str, fmt: str = "json") -> Path:
    rows = list_registry_entries(base_dir)
    path = Path(output_path)
    if fmt == "csv":
        if rows:
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
        else:
            path.write_text("", encoding="utf-8")
    else:
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return path


def archive_registry_entry(run_id: str, base_dir: str = "models", archive_dir: str | None = None) -> Path:
    run_path = Path(base_dir) / run_id
    if not run_path.exists():
        raise FileNotFoundError(f"Registry run not found: {run_id}")
    archive_root = Path(archive_dir) if archive_dir else Path(base_dir) / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    destination = archive_root / run_id
    if destination.exists():
        raise FileExistsError(f"Archive destination already exists: {destination}")
    shutil.move(str(run_path), str(destination))
    return destination


def restore_registry_entry(run_id: str, base_dir: str = "models", archive_dir: str | None = None) -> Path:
    archive_root = Path(archive_dir) if archive_dir else Path(base_dir) / "archive"
    run_path = archive_root / run_id
    if not run_path.exists():
        raise FileNotFoundError(f"Archived registry run not found: {run_id}")
    destination = Path(base_dir) / run_id
    if destination.exists():
        raise FileExistsError(f"Registry destination already exists: {destination}")
    shutil.move(str(run_path), str(destination))
    return destination


def tag_registry_entry(run_id: str, tags: List[str], base_dir: str = "models") -> Path:
    run_path = Path(base_dir) / run_id
    if not run_path.exists():
        raise FileNotFoundError(f"Registry run not found: {run_id}")
    metadata_path = run_path / "metadata.json"
    metadata = _load_json(metadata_path) or {}
    existing = metadata.get("tags") if isinstance(metadata, dict) else []
    merged = sorted({*(existing or []), *tags})
    metadata["tags"] = merged
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect PLL-M model registry entries.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List registry runs")
    list_parser.add_argument("--base-dir", default="models")

    show_parser = subparsers.add_parser("show", help="Show registry run details")
    show_parser.add_argument("run_id")
    show_parser.add_argument("--base-dir", default="models")

    export_parser = subparsers.add_parser("export", help="Export registry list to JSON or CSV")
    export_parser.add_argument("--base-dir", default="models")
    export_parser.add_argument("--output", default="registry_export.json")
    export_parser.add_argument("--format", default="json", choices=["json", "csv"])

    archive_parser = subparsers.add_parser("archive", help="Archive a registry run")
    archive_parser.add_argument("run_id")
    archive_parser.add_argument("--base-dir", default="models")
    archive_parser.add_argument("--archive-dir", default=None)

    restore_parser = subparsers.add_parser("restore", help="Restore an archived registry run")
    restore_parser.add_argument("run_id")
    restore_parser.add_argument("--base-dir", default="models")
    restore_parser.add_argument("--archive-dir", default=None)

    tag_parser = subparsers.add_parser("tag", help="Add tags to a registry run")
    tag_parser.add_argument("run_id")
    tag_parser.add_argument("--tags", required=True, help="Comma-separated tags")
    tag_parser.add_argument("--base-dir", default="models")

    args = parser.parse_args()

    if args.command == "list":
        rows = list_registry_entries(args.base_dir)
        print(json.dumps(rows, indent=2))
    elif args.command == "show":
        payload = show_registry_entry(args.run_id, args.base_dir)
        print(json.dumps(payload, indent=2))
    elif args.command == "export":
        path = export_registry(args.base_dir, args.output, args.format)
        print(f"Registry exported to: {path}")
    elif args.command == "archive":
        destination = archive_registry_entry(args.run_id, args.base_dir, args.archive_dir)
        print(f"Registry run archived to: {destination}")
    elif args.command == "restore":
        destination = restore_registry_entry(args.run_id, args.base_dir, args.archive_dir)
        print(f"Registry run restored to: {destination}")
    elif args.command == "tag":
        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
        metadata_path = tag_registry_entry(args.run_id, tags, args.base_dir)
        print(f"Tags updated in: {metadata_path}")


if __name__ == "__main__":
    main()
