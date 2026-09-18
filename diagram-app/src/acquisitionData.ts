export type JsonPrimitive = string | number | boolean | null;
export type JsonObject = { [key: string]: JsonValue };
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];

export interface AcquisitionAsset {
  id: string;
  label: string;
  shortLabel: string;
  datasetName: string;
  acquisition: JsonObject;
  procedures: JsonObject;
}
export type ComparisonSection = "acquisition" | "procedures";

export interface AcquisitionComparison {
  assets: [AcquisitionAsset, AcquisitionAsset];
}

// Capture this module's own URL so Vite does not rewrite the production path into a
// build-time static asset lookup. The Vite plugin emits this JSON beside the bundle.
const MODULE_URL = import.meta.url;

function comparisonUrl(): string {
  if (import.meta.env.DEV) return "/acquisition-comparison.json";
  return new URL("./acquisition-comparison.json", MODULE_URL).href;
}

let cached: Promise<AcquisitionComparison> | null = null;

export function loadAcquisitionComparison(): Promise<AcquisitionComparison> {
  if (!cached) {
    cached = fetch(comparisonUrl()).then((res) => {
      if (!res.ok) throw new Error(`Failed to load acquisition comparison: ${res.status}`);
      return res.json() as Promise<AcquisitionComparison>;
    });
  }
  return cached;
}
