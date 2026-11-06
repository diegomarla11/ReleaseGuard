export type Status = "pass" | "fail" | "error" | "not_run";
export type Decision = "approved" | "blocked" | "incomplete";
export type CheckKey = "tests" | "build" | "health" | "nonroot" | "scan";
export interface Check {
  status: Status;
  detail: string;
  observed?: unknown;
  counts?: Record<string, number>;
  findings?: {
    id: string | null;
    package: string | null;
    installed: string | null;
    fixed: string | null;
    severity: string;
  }[];
}
export interface Scenario {
  id: string;
  title: string;
  target: string;
  change: string;
  fix: string;
  expected_failure: string | null;
  checks: Record<CheckKey, Check>;
  decision: Decision;
  image_id: string | null;
  assertion: { status: Status; mismatches: string[] };
}
export interface Report {
  schema_version: number;
  kind: "laboratory_execution";
  application: string;
  metadata: {
    generated_at: string;
    commit: string | null;
    dirty: boolean;
    origin: string;
    run_url: string | null;
    repository_url: string | null;
    tools: Record<string, string | null>;
  };
  policy: { id: string; rule: string; blocking_severities: string[] };
  scenarios: Scenario[];
  application_decision: Decision;
  laboratory_status: Status;
  files: { path: string; sha256: string }[];
}
export const keys: CheckKey[] = ["tests", "build", "health", "nonroot", "scan"];
export const labels: Record<CheckKey, string> = {
  tests: "Pruebas",
  build: "Imagen Docker",
  health: "Salud de la API",
  nonroot: "Sin privilegios",
  scan: "Vulnerabilidades",
};
export const states: Record<Status, string> = {
  pass: "Superado",
  fail: "Fallo detectado",
  error: "Error de ejecución",
  not_run: "No ejecutado",
};
export const decisions: Record<Decision, string> = {
  approved: "Aprobada",
  blocked: "Bloqueada",
  incomplete: "Sin aprobar",
};
