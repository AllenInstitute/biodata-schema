import type { Modality, Stage } from "./vocabularies";

export type TagDefinition = {
  id: string;
  key: string;
  values: string;
  modalityScope: Modality | "all";
};

export type GroupField = `tag:${string}`;

export type HierarchyField = "modality" | "stage" | GroupField;

export type GroupStep = {
  id: string;
  fields: GroupField[];
};

export type HierarchyStep = {
  id: string;
  fields: HierarchyField[];
  fixed?: boolean;
};

export type FixedSelections = {
  modalities: Modality[];
  stages: Stage[];
};

export type TreeBranch = {
  id: string;
  key: string;
  value: string;
  children: TreeBranch[];
};