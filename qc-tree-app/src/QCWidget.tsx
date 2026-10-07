import { useState, type DragEvent } from "react";
import type {
  FixedSelections,
  GroupField,
  GroupStep,
  HierarchyStep,
  TagDefinition,
  TreeBranch,
} from "./widgetTypes";
import { buildTree, fieldKey, formatDefaultGrouping } from "./widgetTree";
import { MODALITIES, QC_STAGES, type Modality, type Stage } from "./vocabularies";

const FIELD_DRAG_TYPE = "application/x-qc-tree-field";
const STEP_DRAG_TYPE = "application/x-qc-tree-step";

const initialTags: TagDefinition[] = [
  { id: "probe", key: "probe", values: "A, B", modalityScope: "ecephys" },
  { id: "video", key: "video", values: "left body, right body", modalityScope: "behavior-videos" },
  { id: "shank", key: "shank", values: "0, 1", modalityScope: "ecephys" },
];

const initialGrouping: GroupStep[] = [
  { id: "group-probe-video", fields: ["tag:probe", "tag:video"] },
  { id: "group-shank", fields: ["tag:shank"] },
];

const initialModalities: Modality[] = ["ecephys", "behavior", "behavior-videos"];
const initialStages: Stage[] = ["Raw data", "Processing"];

function makeId(): string {
  return crypto.randomUUID();
}

function toggleValue<Value extends string>(values: Value[], value: Value): Value[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function getFieldOptions(tags: TagDefinition[]): GroupField[] {
  const options: GroupField[] = [];
  const seenKeys = new Set<string>();

  for (const tag of tags) {
    const key = tag.key.trim();
    if (!key || seenKeys.has(key)) continue;
    seenKeys.add(key);
    options.push(`tag:${tag.id}`);
  }

  return options;
}

function TreeList({ branches, root = false }: { branches: TreeBranch[]; root?: boolean }) {
  if (!branches.length) return null;

  return (
    <ul className="qc-tree-list" role={root ? "tree" : "group"}>
      {branches.map((branch) => (
        <li className="qc-tree-branch" key={branch.id} role="treeitem">
          <div className="qc-tree-entry">
            <code>{branch.key}</code>
            <span>{branch.value}</span>
          </div>
          <TreeList branches={branch.children} />
        </li>
      ))}
    </ul>
  );
}

export default function QCWidget() {
  const [tags, setTags] = useState(initialTags);
  const [grouping, setGrouping] = useState(initialGrouping);
  const [modalities, setModalities] = useState(initialModalities);
  const [stages, setStages] = useState<Stage[]>(initialStages);
  const selections: FixedSelections = { modalities, stages };
  const effectiveGrouping: HierarchyStep[] = [];
  if (stages.length > 1) {
    effectiveGrouping.push({ id: "fixed-stage", fields: ["stage"], fixed: true });
  }
  if (modalities.length > 1) {
    effectiveGrouping.push({ id: "fixed-modality", fields: ["modality"], fixed: true });
  }
  const fixedGrouping = [...effectiveGrouping];
  effectiveGrouping.push(
    ...grouping
      .filter((step) => step.fields.length > 0)
      .map((step) => ({ ...step, fixed: false })),
  );
  const tree = buildTree(effectiveGrouping, tags, selections);
  const fieldOptions = getFieldOptions(tags);
  const activeFields = new Set(grouping.flatMap((step) => step.fields));
  const availableFields = fieldOptions.filter((field) => !activeFields.has(field));
  const groupingCode = formatDefaultGrouping(effectiveGrouping, tags);

  function removeField(field: GroupField) {
    setGrouping((current) =>
      current.map((step) => ({ ...step, fields: step.fields.filter((item) => item !== field) })),
    );
  }

  function placeField(field: GroupField, targetId?: string) {
    setGrouping((current) => {
      const source = current.find((step) => step.fields.includes(field));
      if (source?.id === targetId) return current;

      const next = current.map((step) => ({
        ...step,
        fields: step.fields.filter((item) => item !== field),
      }));
      const target = next.find((step) => step.id === targetId);

      if (target) {
        return next.map((step) =>
          step.id === targetId ? { ...step, fields: [...step.fields, field] } : step,
        );
      }
      return [...next, { id: makeId(), fields: [field] }];
    });
  }

  function addLevel() {
    setGrouping((current) => [...current, { id: makeId(), fields: [] }]);
  }

  function moveStep(stepId: string, targetId?: string) {
    setGrouping((current) => {
      if (stepId === targetId) return current;
      const sourceIndex = current.findIndex((step) => step.id === stepId);
      if (sourceIndex < 0) return current;

      const next = [...current];
      const [step] = next.splice(sourceIndex, 1);
      const targetIndex = targetId ? next.findIndex((item) => item.id === targetId) : next.length;
      next.splice(targetIndex < 0 ? next.length : targetIndex, 0, step);
      return next;
    });
  }

  function handleDrop(event: DragEvent<HTMLElement>, targetId?: string) {
    event.preventDefault();
    event.stopPropagation();
    const field = event.dataTransfer.getData(FIELD_DRAG_TYPE) as GroupField;
    const stepId = event.dataTransfer.getData(STEP_DRAG_TYPE);

    if (field) placeField(field, targetId);
    else if (stepId) moveStep(stepId, targetId);
  }

  function startFieldDrag(event: DragEvent<HTMLElement>, field: GroupField) {
    event.dataTransfer.effectAllowed = "copyMove";
    event.dataTransfer.setData(FIELD_DRAG_TYPE, field);
  }

  function startStepDrag(event: DragEvent<HTMLButtonElement>, stepId: string) {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData(STEP_DRAG_TYPE, stepId);
  }

  function updateTag(tagId: string, change: Partial<TagDefinition>) {
    setTags((current) => current.map((tag) => (tag.id === tagId ? { ...tag, ...change } : tag)));
  }

  function addTag() {
    setTags((current) => [
      ...current,
      { id: makeId(), key: "", values: "", modalityScope: "all" },
    ]);
  }

  function removeTag(tagId: string) {
    setTags((current) => current.filter((tag) => tag.id !== tagId));
    removeField(`tag:${tagId}`);
  }

  function updateVocabulary<Value extends Modality | Stage>(
    values: Value[],
    value: Value,
    update: (next: Value[]) => void,
  ) {
    update(toggleValue(values, value));
  }

  return (
    <div className="qc-tree-widget">
      <div className="qc-widget-layout">
        <div className="qc-controls">
          <section aria-label="Stage and modality selections" className="qc-vocabulary">
            <fieldset className="qc-stage-picker">
              <legend>Stage values <span>{stages.length} selected</span></legend>
              <div className="qc-stage-options">
                {QC_STAGES.map((stage) => (
                  <label key={stage}>
                    <input
                      checked={stages.includes(stage)}
                      onChange={() => updateVocabulary(stages, stage, setStages)}
                      type="checkbox"
                    />
                    {stage}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="qc-modality-picker">
              <legend>Modality values <span>{modalities.length} selected</span></legend>
              <div className="qc-vocabulary-options">
                {MODALITIES.map((modality) => (
                  <label key={modality.abbreviation} title={modality.name}>
                    <input
                      checked={modalities.includes(modality.abbreviation)}
                      onChange={() =>
                        updateVocabulary(modalities, modality.abbreviation, setModalities)
                      }
                      type="checkbox"
                    />
                    {modality.abbreviation}
                  </label>
                ))}
              </div>
            </fieldset>
          </section>

          <section aria-label="Tag definitions" className="qc-tag-definitions">
            <div className="qc-tag-definitions-title">Tag definitions</div>
            <div className="qc-tag-table">
              <div aria-hidden="true" className="qc-tag-headings">
                <span>key</span>
                <span>values</span>
                <span>modality</span>
                <span />
              </div>
              {tags.map((tag) => (
                <div className="qc-tag-row" key={tag.id}>
                  <input
                    aria-label="Tag key"
                    onChange={(event) => updateTag(tag.id, { key: event.currentTarget.value })}
                    placeholder="tag key"
                    value={tag.key}
                  />
                  <input
                    aria-label={`Values for ${tag.key || "tag"}`}
                    onChange={(event) => updateTag(tag.id, { values: event.currentTarget.value })}
                    placeholder="A, B"
                    value={tag.values}
                  />
                  <select
                    aria-label={`Modality scope for ${tag.key || "tag"}`}
                    onChange={(event) =>
                      updateTag(tag.id, { modalityScope: event.currentTarget.value as TagDefinition["modalityScope"] })
                    }
                    value={tag.modalityScope}
                  >
                    <option value="all">all</option>
                    {MODALITIES.map((modality) => (
                      <option key={modality.abbreviation} value={modality.abbreviation}>
                        {modality.abbreviation}
                      </option>
                    ))}
                  </select>
                  <button
                    aria-label={`Remove ${tag.key || "tag"}`}
                    className="qc-remove-tag"
                    onClick={() => removeTag(tag.id)}
                    type="button"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <button className="qc-add-tag" onClick={addTag} type="button">
              + Add tag
            </button>
          </section>

          <section aria-label="Default grouping" className="qc-grouping">
            <div className="qc-label">default_grouping</div>
            <div className="qc-field-options">
              <div className="qc-field-options-heading">
                <span>Available tags</span>
                <span>Drag keys into a level</span>
              </div>
              <div className="qc-field-option-list">
                {availableFields.map((field) => (
                  <button
                    aria-label={`Add ${fieldKey(field, tags)} to the first level, or drag it to a level`}
                    className="qc-field-option"
                    draggable
                    key={field}
                    onClick={() => placeField(field, grouping[0]?.id)}
                    onDragStart={(event) => startFieldDrag(event, field)}
                    title="Drag this tag key into a level"
                    type="button"
                  >
                    {fieldKey(field, tags)}
                  </button>
                ))}
                {availableFields.length === 0 && (
                  <span className="qc-no-available-tags">All tag keys are in a level</span>
                )}
              </div>
            </div>

            <ol
              aria-label="Default grouping levels"
              className={`qc-grouping-list${fixedGrouping.length + grouping.length ? "" : " is-empty"}`}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => handleDrop(event)}
            >
              {fixedGrouping.map((step, index) => (
                <li className="qc-grouping-step is-fixed" key={step.id}>
                  <span aria-hidden="true" className="qc-fixed-lock">fixed</span>
                  <span className="qc-step-number">{index + 1}</span>
                  <div className="qc-step-fields">
                    {step.fields.map((field) => (
                      <span className="qc-step-field" key={field}>
                        <button className="qc-fixed-field" disabled type="button">
                          {fieldKey(field, tags)}
                        </button>
                      </span>
                    ))}
                  </div>
                </li>
              ))}
              {grouping.map((step, index) => {
                const levelNumber = fixedGrouping.length + index + 1;
                return (
                  <li
                    className="qc-grouping-step qc-level-bucket"
                    key={step.id}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={(event) => handleDrop(event, step.id)}
                  >
                    <div className="qc-level-header">
                      <button
                        aria-label={`Reorder Level ${levelNumber}`}
                        className="qc-drag-handle"
                        draggable
                        onDragStart={(event) => startStepDrag(event, step.id)}
                        title="Drag to reorder this level"
                        type="button"
                      >
                        <span aria-hidden="true">::</span>
                      </button>
                      <strong className="qc-level-title">Level {levelNumber}</strong>
                      <span className="qc-level-hint">Multiple keys form a tuple</span>
                      <button
                        aria-label={`Remove Level ${levelNumber}`}
                        className="qc-remove-level"
                        onClick={() => setGrouping((current) => current.filter((item) => item.id !== step.id))}
                        type="button"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="qc-level-dropzone">
                      {step.fields.map((field) => (
                        <span
                          className="qc-level-tag"
                          draggable
                          key={field}
                          onDragStart={(event) => startFieldDrag(event, field)}
                          title={`Drag ${fieldKey(field, tags)} to another level`}
                        >
                          <code>{fieldKey(field, tags)}</code>
                          <button
                            aria-label={`Remove ${fieldKey(field, tags)} from Level ${levelNumber}`}
                            onClick={() => removeField(field)}
                            type="button"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                      {step.fields.length === 0 && (
                        <span className="qc-drop-hint">Drop tag keys here</span>
                      )}
                    </div>
                  </li>
                );
              })}
              {fixedGrouping.length + grouping.length === 0 && (
                <li className="qc-grouping-empty">Add a level, then drag tag keys into it.</li>
              )}
            </ol>

            <button className="qc-add-level" onClick={addLevel} type="button">
              + Add level
            </button>

            <code aria-live="polite" className="qc-grouping-code">
              {groupingCode}
            </code>
          </section>
        </div>

        <div aria-label="Live tree hierarchy" className="qc-tree-preview">
          {tree.length ? (
            <TreeList branches={tree} root />
          ) : (
            <p className="qc-tree-empty">Choose a grouping field and values to preview the hierarchy.</p>
          )}
        </div>
      </div>
    </div>
  );
}