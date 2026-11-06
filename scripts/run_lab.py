#!/usr/bin/env python3
"""Run measured checks, preserve evidence, and assert the laboratory contract."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

from scripts.policy import POLICY, REQUIRED, assert_scenario, decide, evaluate_scan

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = [
    ("candidate", "runtime", None, "Versión candidata", "La API responde y se ejecuta sin privilegios.", "Mantener todos los controles en verde y revisar el informe de Trivy."),
    ("health-failure", "broken-health", "health", "Fallo de salud", "El endpoint /health devuelve HTTP 503.", "Restaurar /health para devolver HTTP 200 y status: ok. Reconstruir con el target runtime."),
    ("root-user", "root-user", "nonroot", "Usuario privilegiado", "El proceso se ejecuta con UID 0.", "Restaurar USER 10001:10001. Reconstruir con el target runtime."),
]


def run(command, timeout=300):
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return result.returncode, result.stdout
    except FileNotFoundError:
        return 127, f"No disponible: {command[0]}"
    except PermissionError:
        return 126, f"No se puede ejecutar: {command[0]}"
    except subprocess.TimeoutExpired as exc:
        return 124, f"Tiempo límite de {timeout}s excedido.\n{(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else exc.stdout or ''}"


def command_check(command, path, timeout=300):
    code, output = run(command, timeout)
    path.write_text(output)
    return code, output


def check(status, detail, **extra):
    return {"status": status, "detail": detail, **extra}


def metadata():
    code, commit = run(["git", "rev-parse", "HEAD"])
    _, dirty = run(["git", "status", "--porcelain"])
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    tools = {"python": platform.python_version()}
    for package in ("fastapi", "uvicorn", "pytest"):
        try:
            tools[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            tools[package] = None
    for key, command in (("docker", ["docker", "version", "--format", "{{json .}}"]), ("trivy", ["trivy", "--version"])):
        rc, output = run(command, 20)
        tools[key] = output.strip() if rc == 0 else None
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "commit": commit.strip() if code == 0 else None,
            "dirty": bool(dirty.strip()), "origin": "github_actions" if run_id else "local",
            "run_url": f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else None,
            "repository_url": f"https://github.com/{repo}" if repo else None, "tools": tools}


def probe_container(container, output_dir):
    # Run the actual health endpoint inside the isolated network namespace. No host port.
    probe = """import json, urllib.request, urllib.error
try:
 r=urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2)
 print(json.dumps({'http_status':r.status,'body':json.load(r)}))
except urllib.error.HTTPError as e:
 print(json.dumps({'http_status':e.code,'body':e.read().decode()}))
"""
    observations = []
    observed = None
    for _ in range(20):
        rc, output = run(["docker", "exec", container, "python", "-c", probe], 10)
        observations.append(output)
        if rc == 0:
            try:
                observed = json.loads(output)
                break
            except json.JSONDecodeError:
                pass
        time.sleep(1)
    (output_dir / "health.log").write_text("\n".join(observations))
    if observed is None:
        health = check("error", "Sin respuesta HTTP medible; consultar health.log y container.log.")
    else:
        passed = observed.get("http_status") == 200 and observed.get("body") == {"status": "ok"}
        health = check("pass" if passed else "fail", f"HTTP {observed['http_status']} en /health.", observed=observed)
    # Read actual credentials of PID 1, not just the Dockerfile or an override in docker exec.
    rc, output = command_check(["docker", "exec", container, "python", "-c",
        "import json; s=open('/proc/1/status').read(); print(json.dumps({'uids':[int(x) for x in next(l for l in s.splitlines() if l.startswith('Uid:')).split()[1:]]}))"], output_dir / "user.log", 20)
    try:
        uids = json.loads(output)["uids"] if rc == 0 else []
        if len(uids) != 4 or not all(isinstance(uid, int) and uid >= 0 for uid in uids):
            raise ValueError("UIDs incompletos")
        nonroot = check("pass" if all(uid > 0 for uid in uids) else "fail",
                        f"UID real/efectivo/guardado/fs del proceso: {uids}.", observed={"uids": uids})
    except (KeyError, ValueError, TypeError):
        nonroot = check("error", "No se pudieron medir las credenciales de PID 1.")
    # Also exercise the Docker HEALTHCHECK itself, waiting for its real state.
    state = None
    for _ in range(20):
        rc, output = run(["docker", "inspect", "--format", "{{json .State.Health}}", container], 10)
        if rc == 0:
            try:
                state = json.loads(output)
            except json.JSONDecodeError:
                state = None
        if state and state.get("Status") in ("healthy", "unhealthy"):
            break
        time.sleep(1)
    (output_dir / "docker-health.json").write_text(json.dumps(state, indent=2) + "\n")
    if state is None or state.get("Status") not in ("healthy", "unhealthy"):
        health = check("error", "Docker HEALTHCHECK no produjo un estado final.", observed=observed)
    elif health["status"] != "error":
        health["docker_status"] = state["Status"]
        if state["Status"] != "healthy":
            health["status"] = "fail"
        health["detail"] += f" Docker HEALTHCHECK: {state['Status']}."
    return health, nonroot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--export-approved-image", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    # Refuse reuse: old scan files must never be mistaken for new evidence.
    output.mkdir(parents=True, exist_ok=False)
    meta = metadata()
    test_code, _ = command_check([sys.executable, "-m", "pytest", "--junitxml", str(output / "tests.xml"), "-q"], output / "tests.log")
    test_result = check("pass" if test_code == 0 else "fail", f"pytest terminó con código {test_code}.")
    try:
        suites = ET.parse(output / "tests.xml").getroot()
        test_result["observed"] = {k: sum(int(s.get(k, 0)) for s in suites.iter("testsuite")) for k in ("tests", "failures", "errors", "skipped")}
    except (OSError, ET.ParseError):
        test_result = check("error", "No se generó el informe JUnit de pytest.")
    docker_ready, docker_info = run(["docker", "info", "--format", "{{.ServerVersion}}"], 20)
    (output / "docker-preflight.log").write_text(docker_info)
    report = {"schema_version": 1, "kind": "laboratory_execution", "application": "ReleaseGuard Lab API 1.0.0",
              "metadata": meta, "policy": POLICY, "scenarios": []}
    nonce = uuid.uuid4().hex[:10]
    candidate_image = None
    images = []
    try:
        for scenario_id, target, expected, title, change, fix in SCENARIOS:
            directory = output / scenario_id
            directory.mkdir()
            checks = {key: check("not_run", "No ejecutado: requiere una imagen y Docker disponible.") for key in REQUIRED}
            checks["tests"] = deepcopy(test_result)
            image_id = None
            if docker_ready == 0:
                image = f"releaseguard-lab:{nonce}-{scenario_id}"
                images.append(image)
                rc, _ = command_check(["docker", "build", "--target", target, "--tag", image, "."], directory / "build.log", 600)
                checks["build"] = check("pass" if rc == 0 else "error", f"docker build terminó con código {rc}.")
                if rc == 0:
                    _, identity = command_check(["docker", "image", "inspect", image], directory / "image.json", 20)
                    try:
                        image_id = json.loads(identity)[0]["Id"]
                    except (ValueError, KeyError, IndexError):
                        checks["build"] = check("error", "No se pudo identificar la imagen construida.")
                    container = f"releaseguard-{nonce}-{scenario_id}"
                    try:
                        rc, _ = command_check(["docker", "run", "--detach", "--name", container, "--network", "none",
                            "--read-only", "--cap-drop=ALL", "--security-opt", "no-new-privileges:true", "--pids-limit", "64",
                            "--memory", "256m", "--cpus", "1", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m", image], directory / "start.log", 30)
                        if rc == 0:
                            checks["health"], checks["nonroot"] = probe_container(container, directory)
                        else:
                            checks["health"] = checks["nonroot"] = check("error", "No se pudo iniciar el contenedor.")
                    finally:
                        command_check(["docker", "logs", container], directory / "container.log", 20)
                        run(["docker", "rm", "--force", container], 20)
                    if shutil.which("trivy"):
                        # No severity filter: preserve ALL findings. Policy is evaluated separately.
                        rc, _ = command_check(["trivy", "image", "--image-src", "docker", "--scanners", "vuln",
                            "--format", "json", "--output", str(directory / "trivy.json"), "--exit-code", "0",
                            "--timeout", "5m", image], directory / "trivy.log", 360)
                        if rc == 0:
                            try:
                                checks["scan"] = evaluate_scan(json.loads((directory / "trivy.json").read_text()))
                            except (ValueError, OSError, TypeError, AttributeError) as exc:
                                checks["scan"] = check("error", f"Informe Trivy inválido: {exc}")
                        else:
                            checks["scan"] = check("error", f"Trivy terminó con código {rc}; no se interpreta como limpio.")
                    else:
                        checks["scan"] = check("not_run", "No ejecutado: Trivy no está instalado.")
                    if scenario_id == "candidate":
                        candidate_image = image
            scenario = {"id": scenario_id, "title": title, "target": target, "change": change, "fix": fix,
                        "expected_failure": expected, "checks": checks, "decision": decide(checks), "image_id": image_id,
                        "assertion": assert_scenario(checks, expected)}
            report["scenarios"].append(scenario)
        report["laboratory_status"] = "pass" if all(s["assertion"]["status"] == "pass" for s in report["scenarios"]) else "fail"
        report["application_decision"] = report["scenarios"][0]["decision"]
        if args.export_approved_image and report["application_decision"] == "approved" and candidate_image:
            rc, _ = command_check(["docker", "save", "--output", str(output / "approved-image.tar"), candidate_image], output / "export.log", 120)
            if rc != 0:
                report["laboratory_status"] = "fail"
                report["export_error"] = "No se pudo exportar la imagen aprobada"
        # Capture database metadata AFTER the scan has actually downloaded its DB.
        scanner_code, scanner_version = run(["trivy", "--version"], 20)
        if scanner_code == 0:
            meta["tools"]["trivy"] = scanner_version.strip()
        meta["finished_at"] = datetime.now(timezone.utc).isoformat()
        for scenario in report["scenarios"]:
            print(json.dumps({"scenario": scenario["id"], "decision": scenario["decision"],
                              "checks": {key: value["status"] for key, value in scenario["checks"].items()},
                              "scan_counts": scenario["checks"]["scan"].get("counts")}, ensure_ascii=False))
        # Hash the raw evidence, excluding the optional large image and report itself.
        report["files"] = [{"path": str(p.relative_to(output)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                           for p in sorted(output.rglob("*")) if p.is_file() and p.suffix != ".tar"]
        (output / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"application": report["application_decision"], "laboratory": report["laboratory_status"], "report": str(output / "report.json")}, ensure_ascii=False))
        return 0 if report["laboratory_status"] == "pass" else 1
    finally:
        for image in images:
            run(["docker", "image", "rm", "--force", image], 20)


if __name__ == "__main__":
    raise SystemExit(main())
