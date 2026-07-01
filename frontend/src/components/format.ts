export function metadataText(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export function metadataNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

export function metadataBool(value: unknown): boolean {
  return value === true;
}

export function metadataList(value: unknown): string {
  if (!Array.isArray(value)) {
    return "None";
  }
  const items = value.map((item) => String(item)).filter(Boolean);
  return items.length > 0 ? items.join(", ") : "None";
}

export function metadataObjectList(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    : [];
}

export function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

export function formatTime(value?: string | null): string {
  if (!value) {
    return "N/A";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export function formatNumber(value: number): string {
  return value.toFixed(2);
}

export function formatCost(value: number): string {
  return value === 0 ? "0.0000" : value.toFixed(4);
}

export function shortHash(value?: string | null, length = 12): string {
  if (!value) {
    return "None";
  }
  return value.slice(0, length);
}

export function normalizeRisk(value?: string | null): "LOW_RISK" | "MEDIUM_RISK" | "HIGH_RISK" | "NORMAL" {
  const risk = (value || "").toLowerCase();
  if (risk === "high" || risk === "critical") {
    return "HIGH_RISK";
  }
  if (risk === "medium") {
    return "MEDIUM_RISK";
  }
  if (risk === "low") {
    return "LOW_RISK";
  }
  return "NORMAL";
}

export function normalizeStatus(value?: string | null): string {
  return (value || "unknown").replace(/_/g, " ");
}
