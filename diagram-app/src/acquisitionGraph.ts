import dagre from "dagre";
import type { Edge, Node } from "@xyflow/react";
import type { AcquisitionAsset, AcquisitionComparison, ComparisonSection, JsonObject, JsonValue } from "./acquisitionData";

export const ACQUISITION_NODE_WIDTH = 460;
export const ACQUISITION_HEADER_H = 70;
export const ACQUISITION_ROW_H = 44;
const PADDING_BOTTOM = 8;
const RANK_SEP = 100;
const NODE_SEP = 28;
const MIN_GAP = 40;
export const SAME_COLOR = "#64748b";
export const POPHYS_COLOR = "#0284c7";
export const ECEPHYS_COLOR = "#ea580c";
export const DIFFERENCE_COLOR = "#7c3aed";
export const ROOT_COLOR = "#334155";
export const BASE_TURN = 24;
export const LANE_STEP = 16;

export type Side = "l" | "r";
export type PathSegment = string | number;

export interface ComparisonRow {
  path: PathSegment[];
  pathKey: string;
  segment: PathSegment;
  label: string;
  left: JsonValue | undefined;
  right: JsonValue | undefined;
  same: boolean;
  expandable: boolean;
}

interface AcquisitionInstance {
  id: string;
  path: PathSegment[];
  parentId: string | null;
  side: Side | null;
  rows: ComparisonRow[];
}

interface AcquisitionBuiltEdge {
  id: string;
  source: string;
  sourceHandle: string;
  target: string;
  targetHandle: string;
  rowPathKey: string;
  difference: boolean;
  lane: number;
}

export interface AcquisitionNodeData extends Record<string, unknown> {
  title: string;
  path: PathSegment[];
  rows: ComparisonRow[];
  side: Side | null;
  rowSides: Record<string, Side>;
  assets: [AcquisitionAsset, AcquisitionAsset];
  expandedPaths: Set<string>;
  onTogglePath: (pathKey: string) => void;
  isRoot: boolean;
}

export function pathKey(path: PathSegment[]): string {
  return JSON.stringify(path);
}

function nodeId(path: PathSegment[]): string {
  return path.length === 0 ? "root" : `acquisition-${pathKey(path)}`;
}

function segmentKey(segment: PathSegment): string {
  return encodeURIComponent(JSON.stringify(segment));
}

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isContainer(value: unknown): value is JsonObject | JsonValue[] {
  return Array.isArray(value) || isObject(value);
}
function isExpandableValue(left: JsonValue | undefined, right: JsonValue | undefined): boolean {
  for (const value of [left, right]) {
    if (isObject(value)) return true;
    if (Array.isArray(value) && (value.length !== 1 || value.some((item) => isContainer(item)))) return true;
  }
  return false;
}

function valueAt(value: JsonValue, path: PathSegment[]): JsonValue | undefined {
  let current: JsonValue | undefined = value;
  for (const segment of path) {
    if (Array.isArray(current) && typeof segment === "number") {
      current = current[segment];
    } else if (isObject(current) && typeof segment === "string") {
      current = current[segment];
    } else {
      return undefined;
    }
  }
  return current;
}

function equalValues(left: JsonValue | undefined, right: JsonValue | undefined): boolean {
  if (left === right) return true;
  if (left === undefined || right === undefined || left === null || right === null) return false;
  if (Array.isArray(left) || Array.isArray(right)) {
    if (!Array.isArray(left) || !Array.isArray(right) || left.length !== right.length) return false;
    return left.every((value, index) => equalValues(value, right[index]));
  }
  if (isObject(left) || isObject(right)) {
    if (!isObject(left) || !isObject(right)) return false;
    const leftKeys = Object.keys(left);
    const rightKeys = Object.keys(right);
    if (leftKeys.length !== rightKeys.length) return false;
    return leftKeys.every((key) => key in right && equalValues(left[key], right[key]));
  }
  return false;
}

function childSegments(left: JsonValue | undefined, right: JsonValue | undefined): PathSegment[] {
  if (Array.isArray(left) || Array.isArray(right)) {
    const length = Math.max(left instanceof Array ? left.length : 0, right instanceof Array ? right.length : 0);
    return Array.from({ length }, (_, index) => index);
  }

  if (isObject(left) || isObject(right)) {
    const keys = new Set<string>();
    if (isObject(left)) Object.keys(left).forEach((key) => keys.add(key));
    if (isObject(right)) Object.keys(right).forEach((key) => keys.add(key));
    return [...keys];
  }

  return [];
}

function displaySegment(segment: PathSegment): string {
  return typeof segment === "number" ? `[${segment}]` : segment;
}

function rowsForPath(comparison: AcquisitionComparison, section: ComparisonSection, path: PathSegment[]): ComparisonRow[] {
  const leftParent = valueAt(comparison.assets[0][section], path);
  const rightParent = valueAt(comparison.assets[1][section], path);
  return childSegments(leftParent, rightParent).flatMap((segment) => {
    const childPath = [...path, segment];
    const left = valueAt(comparison.assets[0][section], childPath);
    const right = valueAt(comparison.assets[1][section], childPath);
    if (
      (left === null && right === null) ||
      (Array.isArray(left) && Array.isArray(right) && left.length === 0 && right.length === 0)
    ) return [];
    return [{
      path: childPath,
      pathKey: pathKey(childPath),
      segment,
      label: displaySegment(segment),
      left,
      right,
      same: equalValues(left, right),
      expandable: isExpandableValue(left, right),
    }];
  });
}

export function computeSeedExpansion(comparison: AcquisitionComparison, section: ComparisonSection): Set<string> {
  const seed = new Set<string>();
  const rootRows = rowsForPath(comparison, section, []);
  for (const row of rootRows) {
    // Keep large epoch/device collections collapsed on first load so the comparison
    // remains readable; clicking the row still exposes the complete metadata.
    if (row.expandable && childSegments(row.left, row.right).length <= 12) seed.add(row.pathKey);
  }

  if (section === "acquisition") {
    // Show the data stream object itself on first load: data_streams -> [0].
    const dataStreams = rootRows.find((row) => row.segment === "data_streams");
    if (dataStreams?.expandable) {
      seed.add(dataStreams.pathKey);
      const firstStream = rowsForPath(comparison, section, dataStreams.path).find((row) => row.segment === 0);
      if (firstStream?.expandable) seed.add(firstStream.pathKey);
    }
  }
  return seed;
}

function estimateHeight(instance: AcquisitionInstance): number {
  return ACQUISITION_HEADER_H + instance.rows.length * ACQUISITION_ROW_H + PADDING_BOTTOM;
}

function outwardClearance(instanceId: string, edges: AcquisitionBuiltEdge[]): number {
  let maxLane = -1;
  for (const edge of edges) {
    if (edge.source !== instanceId) continue;
    maxLane = Math.max(maxLane, edge.lane);
  }
  return maxLane < 0 ? 0 : BASE_TURN + maxLane * LANE_STEP + 24;
}

function assignLanes(
  instances: AcquisitionInstance[],
  edges: AcquisitionBuiltEdge[],
  instancesById: Map<string, AcquisitionInstance>,
  centerY: Map<string, number>,
) {
  const bySourceAndSide = new Map<string, AcquisitionBuiltEdge[]>();
  for (const edge of edges) {
    const targetSide = instancesById.get(edge.target)?.side;
    if (!targetSide) continue;
    const key = `${edge.source}|${targetSide}`;
    const group = bySourceAndSide.get(key) ?? [];
    group.push(edge);
    bySourceAndSide.set(key, group);
  }

  for (const group of bySourceAndSide.values()) {
    const source = instancesById.get(group[0].source);
    if (!source) continue;
    const sourceTop = (centerY.get(source.id) ?? 0) - estimateHeight(source) / 2;
    const withDirection = group.map((edge) => {
      const rowIndex = Math.max(0, source.rows.findIndex((row) => row.pathKey === edge.rowPathKey));
      const rowY = sourceTop + ACQUISITION_HEADER_H + rowIndex * ACQUISITION_ROW_H + ACQUISITION_ROW_H / 2;
      const targetCenterY = centerY.get(edge.target) ?? 0;
      return { edge, isUp: targetCenterY < rowY };
    });
    const up = withDirection.filter((entry) => entry.isUp);
    const down = withDirection.filter((entry) => !entry.isUp);
    up.forEach((entry, index) => (entry.edge.lane = index));
    down.forEach((entry, index) => (entry.edge.lane = down.length - 1 - index));
  }
}

function layoutSide(
  instances: AcquisitionInstance[],
  edges: AcquisitionBuiltEdge[],
  side: Side,
  instancesById: Map<string, AcquisitionInstance>,
  colX: number,
): Map<string, { x: number; y: number }> {
  const group = instances.filter((instance) => instance.side === side);
  const positions = new Map<string, { x: number; y: number }>();
  if (group.length === 0) return positions;

  const graph = new dagre.graphlib.Graph();
  graph.setGraph({ rankdir: "LR", nodesep: NODE_SEP, ranksep: RANK_SEP });
  graph.setDefaultEdgeLabel(() => ({}));
  const idSet = new Set(group.map((instance) => instance.id));
  for (const instance of group) {
    const clearance = outwardClearance(instance.id, edges);
    graph.setNode(instance.id, {
      width: ACQUISITION_NODE_WIDTH + 2 * clearance,
      height: estimateHeight(instance),
    });
  }
  for (const edge of edges) {
    if (idSet.has(edge.source) && idSet.has(edge.target)) graph.setEdge(edge.source, edge.target);
  }
  dagre.layout(graph);

  const topLevel = group.filter((instance) => instance.parentId === "root");
  const referenceX = topLevel.length ? graph.node(topLevel[0].id).x : 0;
  const averageY = topLevel.length
    ? topLevel.reduce((sum, instance) => sum + graph.node(instance.id).y, 0) / topLevel.length
    : 0;

  for (const instance of group) {
    const node = graph.node(instance.id);
    const dx = node.x - referenceX;
    positions.set(instance.id, {
      x: side === "l" ? -colX - dx : colX + dx,
      y: node.y - averageY,
    });
  }
  return positions;
}

function computePositions(instances: AcquisitionInstance[], edges: AcquisitionBuiltEdge[]) {
  const instancesById = new Map(instances.map((instance) => [instance.id, instance]));
  const preliminaryLeft = layoutSide(instances, edges, "l", instancesById, ACQUISITION_NODE_WIDTH + MIN_GAP);
  const preliminaryRight = layoutSide(instances, edges, "r", instancesById, ACQUISITION_NODE_WIDTH + MIN_GAP);
  const centerY = new Map<string, number>([["root", 0]]);
  for (const instance of instances) {
    const position = (instance.side === "l" ? preliminaryLeft : preliminaryRight).get(instance.id);
    if (position) centerY.set(instance.id, position.y);
  }
  assignLanes(instances, edges, instancesById, centerY);

  const rootClearance = outwardClearance("root", edges);
  const colX = ACQUISITION_NODE_WIDTH + rootClearance + MIN_GAP;
  const left = layoutSide(instances, edges, "l", instancesById, colX);
  const right = layoutSide(instances, edges, "r", instancesById, colX);
  const result = new Map<string, { x: number; y: number }>();
  for (const instance of instances) {
    const center = instance.id === "root" ? { x: 0, y: 0 } : (instance.side === "l" ? left : right).get(instance.id) ?? { x: 0, y: 0 };
    result.set(instance.id, {
      x: center.x - ACQUISITION_NODE_WIDTH / 2,
      y: center.y - estimateHeight(instance) / 2,
    });
  }
  return result;
}

export function buildAcquisitionGraph(
  comparison: AcquisitionComparison,
  section: ComparisonSection,
  expandedPaths: Set<string>,
  onTogglePath: (pathKey: string) => void,
): { nodes: Node<AcquisitionNodeData>[]; edges: Edge[] } {
  const instances: AcquisitionInstance[] = [];
  const builtEdges: AcquisitionBuiltEdge[] = [];
  const rootRows = rowsForPath(comparison, section, []);
  const root: AcquisitionInstance = { id: "root", path: [], parentId: null, side: null, rows: rootRows };
  instances.push(root);

  const rootExpandable = rootRows.filter((row) => row.expandable);
  const rootSides = new Map<string, Side>();
  rootExpandable.forEach((row, index) => rootSides.set(row.pathKey, index % 2 === 0 ? "l" : "r"));

  function walk(parent: AcquisitionInstance) {
    for (const row of parent.rows) {
      if (!row.expandable || !expandedPaths.has(row.pathKey)) continue;
      const side = parent.id === "root" ? rootSides.get(row.pathKey)! : parent.side!;
      const child: AcquisitionInstance = {
        id: nodeId(row.path),
        path: row.path,
        parentId: parent.id,
        side,
        rows: rowsForPath(comparison, section, row.path),
      };
      instances.push(child);
      builtEdges.push({
        id: `edge-${child.id}`,
        source: parent.id,
        sourceHandle: `out-${segmentKey(row.segment)}`,
        target: child.id,
        targetHandle: "in",
        rowPathKey: row.pathKey,
        difference: !row.same,
        lane: 0,
      });
      walk(child);
    }
  }
  walk(root);

  const positions = computePositions(instances, builtEdges);
  const rowSides: Record<string, Side> = {};
  rootSides.forEach((side, key) => (rowSides[key] = side));
  const nodes: Node<AcquisitionNodeData>[] = instances.map((instance) => {
    const title = instance.id === "root" ? (section === "acquisition" ? "Acquisition" : "Procedures") : displaySegment(instance.path[instance.path.length - 1]);
    const localRowSides: Record<string, Side> = instance.id === "root" ? rowSides : {};
    if (instance.id !== "root" && instance.side) {
      instance.rows.forEach((row) => (localRowSides[row.pathKey] = instance.side!));
    }
    return {
      id: instance.id,
      type: "acquisition",
      position: positions.get(instance.id) ?? { x: 0, y: 0 },
      width: ACQUISITION_NODE_WIDTH,
      height: estimateHeight(instance),
      data: {
        title,
        path: instance.path,
        rows: instance.rows,
        side: instance.side,
        rowSides: localRowSides,
        assets: comparison.assets,
        expandedPaths,
        onTogglePath,
        isRoot: instance.id === "root",
      },
    };
  });

  const edges: Edge[] = builtEdges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    sourceHandle: edge.sourceHandle,
    target: edge.target,
    targetHandle: edge.targetHandle,
    type: "circuit",
    data: { lane: edge.lane },
    style: {
      stroke: edge.difference ? DIFFERENCE_COLOR : SAME_COLOR,
      strokeWidth: edge.difference ? 2 : 1.5,
    },
  }));

  return { nodes, edges };
}
