import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  Background,
  Controls,
  Panel,
  ReactFlow,
  useReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import { edgeTypes } from "./edges";
import { loadAcquisitionComparison, type AcquisitionComparison, type ComparisonSection } from "./acquisitionData";
import {
  buildAcquisitionGraph,
  computeSeedExpansion,
  ECEPHYS_COLOR,
  POPHYS_COLOR,
  SAME_COLOR,
  type AcquisitionNodeData,
} from "./acquisitionGraph";
import { acquisitionNodeTypes } from "./acquisitionNodes";

interface ComparisonViewerProps {
  section?: ComparisonSection;
}

function AcquisitionViewer({ section = "acquisition" }: ComparisonViewerProps) {
  const sectionLabel = section === "acquisition" ? "Acquisition" : "Procedures";
  const [comparison, setComparison] = useState<AcquisitionComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const hasFitOnce = useRef(false);
  const { fitView } = useReactFlow();
  // This comparison surface is intentionally light regardless of the host site's theme.
  const isDark = false;

  useEffect(() => {
    let cancelled = false;
    loadAcquisitionComparison()
      .then((data) => {
        if (cancelled) return;
        setComparison(data);
        setExpandedPaths(computeSeedExpansion(data, section));
      })
      .catch((reason) => !cancelled && setError(String(reason)));
    return () => {
      cancelled = true;
    };
  }, [section]);

  useEffect(() => {
    const onFullscreenChange = () => setIsFullscreen(document.fullscreenElement === wrapperRef.current);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (document.fullscreenElement) document.exitFullscreen();
    else wrapperRef.current?.requestFullscreen();
  }, []);

  const togglePath = useCallback((path: string) => {
    setExpandedPaths((previous) => {
      const next = new Set(previous);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }, []);

  const resetExpansion = useCallback(() => {
    if (comparison) setExpandedPaths(computeSeedExpansion(comparison, section));
  }, [comparison, section]);

  const graph = useMemo(() => {
    if (!comparison) return null;
    return buildAcquisitionGraph(comparison, section, expandedPaths, togglePath);
  }, [comparison, section, expandedPaths, togglePath]);

  useEffect(() => {
    if (!graph || hasFitOnce.current) return;
    const timeout = window.setTimeout(() => {
      hasFitOnce.current = true;
      fitView({ padding: 0.12, maxZoom: 1 });
    }, 100);
    return () => window.clearTimeout(timeout);
  }, [graph, fitView]);

  useEffect(() => {
    if (!hasFitOnce.current) return;
    const frame = requestAnimationFrame(() => fitView({ padding: 0.12, maxZoom: 1, duration: 300 }));
    return () => cancelAnimationFrame(frame);
  }, [isFullscreen, fitView]);

  if (error) {
    return <div style={{ padding: 16, color: "#b91c1c", fontFamily: "sans-serif" }}>Failed to load {sectionLabel.toLowerCase()} comparison: {error}</div>;
  }
  if (!comparison || !graph) {
    return <div style={{ padding: 16, fontFamily: "sans-serif", color: "#6b7280" }}>Loading {sectionLabel.toLowerCase()} comparison…</div>;
  }

  return (
    <div
      ref={wrapperRef}
      style={
        {
          width: "100%",
          height: isFullscreen ? "100vh" : "100%",
          background: "var(--schema-page-bg)",
          "--schema-page-bg": isDark ? "#000" : "#fff",
          "--schema-card-bg": isDark ? "#000" : "#fff",
          "--schema-card-text": isDark ? "#fff" : "#111827",
          "--schema-card-divider": isDark ? "#27272a" : "#e2e8f0",
          "--schema-difference-bg": isDark ? "#1e1533" : "#faf5ff",
          "--schema-dot-color": isDark ? "#3f3f46" : "#a1a1aa",
        } as CSSProperties
      }
    >
      <ReactFlow
        nodes={graph.nodes as Node<AcquisitionNodeData>[]}
        edges={graph.edges as Edge[]}
        nodeTypes={acquisitionNodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        minZoom={0.01}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--schema-dot-color)" />
        <Controls showInteractive={false} />
        <Panel position="top-left" style={legendStyle}>
          <strong style={{ fontSize: 13 }}>{sectionLabel} metadata comparison</strong>
          <span style={{ color: "#64748b", fontSize: 11 }}>Click + rows to drill into nested {sectionLabel.toLowerCase()} fields.</span>
          <div style={{ display: "flex", gap: 12, fontSize: 11, marginTop: 4 }}>
            <span><i style={{ ...legendSwatch, background: SAME_COLOR }} />same</span>
            <span><i style={{ ...legendSwatch, background: POPHYS_COLOR }} />{comparison.assets[0].shortLabel}</span>
            <span><i style={{ ...legendSwatch, background: ECEPHYS_COLOR }} />{comparison.assets[1].shortLabel}</span>
          </div>
        </Panel>
        <Panel position="top-right" style={{ display: "flex", gap: 8 }}>
          <button onClick={() => fitView({ padding: 0.12, maxZoom: 1, duration: 300 })} style={panelButtonStyle}>Fit view</button>
          <button onClick={resetExpansion} style={panelButtonStyle}>Reset nested fields</button>
          <button onClick={toggleFullscreen} style={panelButtonStyle}>{isFullscreen ? "Exit fullscreen" : "Fullscreen ⛶"}</button>
        </Panel>
      </ReactFlow>
    </div>
  );
}

const legendStyle: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 3,
  padding: "8px 10px",
  borderRadius: 7,
  background: "var(--schema-card-bg, #fff)",
  color: "var(--schema-card-text, #111827)",
  border: "1px solid #cbd5e1",
  boxShadow: "0 1px 3px rgba(15,23,42,0.12)",
};

const legendSwatch: CSSProperties = {
  display: "inline-block",
  width: 8,
  height: 8,
  borderRadius: "50%",
  marginRight: 4,
};

const panelButtonStyle: CSSProperties = {
  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  fontSize: 12,
  fontWeight: 600,
  padding: "6px 10px",
  borderRadius: 6,
  border: "1px solid #c7d2fe",
  background: "#fff",
  color: "#3730a3",
  cursor: "pointer",
  boxShadow: "0 1px 2px rgba(15,23,42,0.08)",
};

export default AcquisitionViewer;
