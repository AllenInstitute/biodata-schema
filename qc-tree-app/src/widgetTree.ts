import type { FixedSelections, HierarchyField, HierarchyStep, TagDefinition, TreeBranch } from "./widgetTypes";
import type { Modality, Stage } from "./vocabularies";

type TreeContext = {
  modality?: Modality;
  stage?: Stage;
};

type Candidate = {
  key: string;
  value: string;
  context: TreeContext;
};

export function fieldKey(field: HierarchyField, tags: TagDefinition[]): string {
  if (field === "modality" || field === "stage") return field;
  return tags.find((tag) => `tag:${tag.id}` === field)?.key.trim() || "tag";
}

export function formatDefaultGrouping(grouping: HierarchyStep[], tags: TagDefinition[]): string {
  const entries = grouping.map((step) => {
    const keys = step.fields.map((field) => JSON.stringify(fieldKey(field, tags)));
    return keys.length === 1 ? keys[0] : `(${keys.join(", ")})`;
  });

  return `default_grouping = [${entries.join(", ")}]`;
}

function candidatesForField(
  field: HierarchyField,
  context: TreeContext,
  tags: TagDefinition[],
  selections: FixedSelections,
): Candidate[] {
  if (field === "modality") {
    if (context.modality) return [];
    return selections.modalities.map((value) => ({
      key: "modality",
      value,
      context: { ...context, modality: value },
    }));
  }

  if (field === "stage") {
    if (context.stage) return [];
    return selections.stages.map((value) => ({
      key: "stage",
      value,
      context: { ...context, stage: value },
    }));
  }

  const tag = tags.find((item) => `tag:${item.id}` === field);
  if (!tag || (context.modality && tag.modalityScope !== "all" && tag.modalityScope !== context.modality)) {
    return [];
  }

  return Array.from(new Set(tag.values.split(",").map((value) => value.trim()).filter(Boolean))).map((value) => ({
    key: fieldKey(field, tags),
    value,
    context,
  }));
}

function buildLevel(
  grouping: HierarchyStep[],
  tags: TagDefinition[],
  selections: FixedSelections,
  depth: number,
  context: TreeContext,
): TreeBranch[] {
  const step = grouping[depth];
  if (!step) return [];

  return step.fields.flatMap((field) =>
    candidatesForField(field, context, tags, selections).map((candidate) => ({
      id: `${step.id}:${field}:${candidate.value}`,
      key: candidate.key,
      value: candidate.value,
      children: buildLevel(grouping, tags, selections, depth + 1, candidate.context),
    })),
  );
}

export function buildTree(
  grouping: HierarchyStep[],
  tags: TagDefinition[],
  selections: FixedSelections,
): TreeBranch[] {
  const context = {
    ...(selections.modalities.length === 1 ? { modality: selections.modalities[0] } : {}),
    ...(selections.stages.length === 1 ? { stage: selections.stages[0] } : {}),
  };
  return buildLevel(grouping, tags, selections, 0, context);
}