import type { StatusBadgeKind } from "./componentTypes";

const defaultLabels: Record<StatusBadgeKind, string> = {
  REAL_LOCAL: "REAL_LOCAL",
  MOCK_ONLY: "MOCK_ONLY",
  RESERVED_DISABLED: "RESERVED_DISABLED",
  NO_EXTERNAL_CALL: "NO_EXTERNAL_CALL",
  NO_DESKTOP_EXECUTION: "NO_DESKTOP_EXECUTION",
  REQUIRES_APPROVAL: "REQUIRES_APPROVAL",
  BLOCKED: "BLOCKED",
  RUNNING: "RUNNING",
  COMPLETED: "COMPLETED",
  FAILED: "FAILED",
  PAUSED: "PAUSED",
  LOW_RISK: "LOW_RISK",
  MEDIUM_RISK: "MEDIUM_RISK",
  HIGH_RISK: "HIGH_RISK",
  NORMAL: "NORMAL"
};

type StatusBadgeProps = {
  kind: StatusBadgeKind;
  label?: string;
};

export function StatusBadge({ kind, label }: StatusBadgeProps) {
  return <span className={`status-badge status-${kind.toLowerCase()}`}>{label || defaultLabels[kind]}</span>;
}
