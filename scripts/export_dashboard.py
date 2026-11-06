"""Copy only the allowlisted evidence referenced by the report; never an image or secrets."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from scripts.policy import REQUIRED, decide


def validate(report, source):
    if report.get("schema_version") != 1 or report.get("kind") != "laboratory_execution":
        raise ValueError("Formato de evidencia no compatible")
    scenarios = report.get("scenarios", [])
    if {s["id"] for s in scenarios} != {"candidate", "health-failure", "root-user"} or len(scenarios) != 3:
        raise ValueError("Deben existir los tres escenarios")
    for scenario in scenarios:
        if set(scenario["checks"]) != set(REQUIRED) or scenario["decision"] != decide(scenario["checks"]):
            raise ValueError("Decisión inconsistente con los controles")
    for file in report["files"]:
        relative = Path(file["path"])
        path = (source / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(source.resolve()) or path.suffix not in (".json", ".xml", ".log"):
            raise ValueError("Ruta de evidencia no permitida")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != file["sha256"]:
            raise ValueError(f"Integridad incorrecta: {relative}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    report = json.loads((args.source / "report.json").read_text())
    validate(report, args.source)
    args.destination.mkdir(parents=True, exist_ok=True)
    # Clear old generated evidence, preventing orphaned reports from being published.
    for child in args.destination.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for file in [*report["files"], {"path": "report.json"}]:
        destination = args.destination / file["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.source / file["path"], destination)
    print(f"Evidencias verificadas y exportadas: {args.destination}")


if __name__ == "__main__":
    main()
