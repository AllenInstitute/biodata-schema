import { Handle, Position, type NodeProps, type NodeTypes } from "@xyflow/react";
import {
  ACQUISITION_HEADER_H,
  ACQUISITION_NODE_WIDTH,
  ACQUISITION_ROW_H,
  DIFFERENCE_COLOR,
  ECEPHYS_COLOR,
  POPHYS_COLOR,
  ROOT_COLOR,
  SAME_COLOR,
  type AcquisitionNodeData,
  type ComparisonRow,
  type Side,
} from "./acquisitionGraph";

const FONT = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
const MONO = '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace';
const CARD_SHADOW = "0 1px 2px rgba(15,23,42,0.08), 0 2px 6px rgba(15,23,42,0.10)";
const HANDLE_STYLE = { opacity: 0, width: 1, height: 1, border: 0, minWidth: 0, minHeight: 0 };


function displayValue(value: unknown): string {
  if (value === undefined) return "—";
  if (value === null) return "null";
  if (Array.isArray(value)) {
    if (value.length === 1 && (value[0] === null || typeof value[0] !== "object")) return displayValue(value[0]);
    return `[${value.length} ${value.length === 1 ? "item" : "items"}]`;
  }
  if (typeof value === "object" && value !== null) {
    const count = Object.keys(value).length;
    return `{${count} ${count === 1 ? "field" : "fields"}}`;
  }
  const text = String(value).replace(/\s+/g, " ");
  return text.length > 46 ? `${text.slice(0, 45)}…` : text;
}

function fullValue(value: unknown): string {
  if (value === undefined) return "missing";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function rowValueColor(row: ComparisonRow, assetIndex: 0 | 1): string {
  if (row.same) return SAME_COLOR;
  return assetIndex === 0 ? POPHYS_COLOR : ECEPHYS_COLOR;
}

function AcquisitionNode({ data }: NodeProps) {
  const d = data as AcquisitionNodeData;
  const hasDifference = d.rows.some((row) => !row.same);
  const headerColor = d.isRoot ? ROOT_COLOR : hasDifference ? DIFFERENCE_COLOR : SAME_COLOR;
  const pathLabel = d.path.length ? d.path.map((segment) => (typeof segment === "number" ? `[${segment}]` : segment)).join(" › ") : "all acquisition fields";

  return (
    <div
      style={{
        width: ACQUISITION_NODE_WIDTH,
        height: "100%",
        boxSizing: "border-box",
        background: "var(--schema-card-bg, #fff)",
        border: `2px solid ${headerColor}`,
        borderRadius: 8,
        boxShadow: CARD_SHADOW,
        fontFamily: FONT,
        overflow: "visible",
        position: "relative",
        pointerEvents: "auto",
      }}
    >
      {d.side ? (
        <Handle
          type="target"
          id="in"
          position={d.side === "l" ? Position.Right : Position.Left}
          style={HANDLE_STYLE}
          isConnectable={false}
        />
      ) : null}

      <div
        style={{
          height: ACQUISITION_HEADER_H,
          boxSizing: "border-box",
          padding: "8px 8px 7px",
          background: headerColor,
          color: "#fff",
          borderRadius: "5px 5px 0 0",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 7, minWidth: 0 }}>
          <strong style={{ fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {d.title}
          </strong>
          <span
            style={{
              marginLeft: "auto",
              flex: "0 0 auto",
              fontSize: 10,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              opacity: 0.9,
            }}
          >
            {hasDifference ? "different" : "same"}
          </span>
        </div>
        <div style={{ marginTop: 6, display: "grid", gridTemplateColumns: "150px minmax(0, 1fr) minmax(0, 1fr)", gap: 6, fontSize: 10.5 }}>
          <span />
          <span style={{ color: d.assets[0].id === "pophys" ? "#bae6fd" : "#fed7aa", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={d.assets[0].datasetName}>
            {d.assets[0].shortLabel}
          </span>
          <span style={{ color: d.assets[1].id === "pophys" ? "#bae6fd" : "#fed7aa", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }} title={d.assets[1].datasetName}>
            {d.assets[1].shortLabel}
          </span>
        </div>
      </div>

      {d.rows.map((row, index) => {
        const expanded = row.expandable && d.expandedPaths.has(row.pathKey);
        const outSide: Side = d.side ?? d.rowSides[row.pathKey] ?? "r";
        const leftText = displayValue(row.left);
        const rightText = displayValue(row.right);
        return (
          <div
            key={row.pathKey}
            onClick={row.expandable ? () => d.onTogglePath(row.pathKey) : undefined}
            className={row.expandable ? "nodrag nopan" : undefined}
            title={`${row.label}\n${d.assets[0].label}: ${fullValue(row.left)}\n${d.assets[1].label}: ${fullValue(row.right)}`}
            style={{
              position: "relative",
              height: ACQUISITION_ROW_H,
              boxSizing: "border-box",
              display: "grid",
              gridTemplateColumns: "150px minmax(0, 1fr) minmax(0, 1fr)",
              alignItems: "center",
              gap: 6,
              padding: "0 8px",
              fontSize: 11,
              borderTop: index === 0 ? "none" : "1px solid var(--schema-card-divider, #e2e8f0)",
              cursor: row.expandable ? "pointer" : "default",
              background: row.same ? "var(--schema-card-bg, #fff)" : "var(--schema-difference-bg, #faf5ff)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 4, minWidth: 0 }}>
              {row.expandable ? (
                <span style={{ color: row.same ? SAME_COLOR : DIFFERENCE_COLOR, fontWeight: 800, fontSize: 17, width: 13, flex: "0 0 auto", lineHeight: 1 }}>
                  {expanded ? "−" : "+"}
                </span>
              ) : (
                <span style={{ width: 13, flex: "0 0 auto" }} />
              )}
              <code style={{ fontFamily: MONO, fontSize: 10.5, color: "var(--schema-card-text, #111827)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {row.label}
              </code>
              {row.expandable ? <span style={{ color: row.same ? SAME_COLOR : DIFFERENCE_COLOR, fontSize: 9 }}>◆</span> : null}
            </div>
            <span style={{ color: rowValueColor(row, 0), overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {leftText}
            </span>
            <span style={{ color: rowValueColor(row, 1), overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {rightText}
            </span>
            {row.expandable ? (
              <Handle
                type="source"
                id={`out-${encodeURIComponent(JSON.stringify(row.segment))}`}
                position={outSide === "l" ? Position.Left : Position.Right}
                style={HANDLE_STYLE}
                isConnectable={false}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export const acquisitionNodeTypes: NodeTypes = {
  acquisition: AcquisitionNode,
};
