"""Pure fail-closed decisions. Scenario names never participate in approval."""
REQUIRED = ("tests", "build", "health", "nonroot", "scan")
POLICY = {
    "id": "releaseguard-v1",
    "blocking_severities": ["HIGH", "CRITICAL"],
    "include_unfixed": True,
    "rule": "Todos los controles deben pasar. HIGH y CRITICAL bloquean, exista o no corrección.",
}


def decide(checks):
    states = [checks.get(key, {}).get("status", "not_run") for key in REQUIRED]
    if any(state == "fail" for state in states):
        return "blocked"
    if all(state == "pass" for state in states):
        return "approved"
    return "incomplete"


def evaluate_scan(document):
    if document.get("SchemaVersion") != 2 or document.get("ArtifactType") != "container_image":
        raise ValueError("No es un informe JSON v2 de imagen Trivy")
    results = document.get("Results")
    if not isinstance(results, list) or not results:
        raise ValueError("Faltan resultados: no se interpreta un informe vacío como seguro")
    # A minimal Python image must contain an OS package inventory to be assessable.
    os_results = [r for r in results if r.get("Class") == "os-pkgs"]
    python_results = [r for r in results if r.get("Type") == "python-pkg"]
    if not any(r.get("Packages") for r in os_results):
        raise ValueError("No se ha identificado el inventario del sistema operativo")
    if not any(p.get("Name") == "fastapi" for r in python_results for p in r.get("Packages", [])):
        raise ValueError("No se ha identificado FastAPI en el inventario Python")
    counts = {severity: 0 for severity in ("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL")}
    findings = []
    for result in results:
        vulnerabilities = result.get("Vulnerabilities") or []
        if not isinstance(vulnerabilities, list):
            raise ValueError("Lista de vulnerabilidades inválida")
        for vuln in vulnerabilities:
            severity = vuln.get("Severity", "UNKNOWN")
            if severity not in counts:
                raise ValueError("Severidad desconocida en el formato del informe")
            counts[severity] += 1
            findings.append({"id": vuln.get("VulnerabilityID"), "package": vuln.get("PkgName"),
                             "installed": vuln.get("InstalledVersion"), "fixed": vuln.get("FixedVersion"),
                             "severity": severity})
    blocked = sum(counts[s] for s in POLICY["blocking_severities"])
    return {"status": "fail" if blocked else "pass", "counts": counts, "findings": findings,
            "detail": f"{blocked} hallazgos HIGH/CRITICAL. Incluye vulnerabilidades sin corrección."}


def assert_scenario(checks, expected_failure):
    """Expected fault is exact; extra failures or unexecuted controls never pass."""
    expected = {key: "fail" if key == expected_failure else "pass" for key in REQUIRED}
    mismatches = [f"{key}: esperado {value}, observado {checks.get(key, {}).get('status', 'not_run')}"
                  for key, value in expected.items() if checks.get(key, {}).get("status") != value]
    return {"status": "pass" if not mismatches else "fail", "mismatches": mismatches}
