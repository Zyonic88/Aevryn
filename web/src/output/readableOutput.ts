const SOURCE_BACKED_PLACEHOLDER = "Source-backed detail available through evidence controls.";

export function readableOutputItems(items: string[]): string[] {
  const readableItems = items
    .filter((item) => !isInternalOutputPlaceholder(item))
    .map(readableOutputItem)
    .filter((item) => item.length > 0)
    .filter((item, index, allItems) => allItems.indexOf(item) === index);
  if (readableItems.length > 1) {
    return readableItems.filter((item) => item !== "Unknown");
  }
  return readableItems;
}

export function readableOutputItem(item: string): string {
  if (isInternalOutputPlaceholder(item)) {
    return "";
  }
  const withoutAnchorPrefix = item.replace(/^aevryn_import_bundle_chapter_\d{3}:\s*/i, "");
  const acceptedEntity = withoutAnchorPrefix.match(/^Entity accepted:\s*(.+)$/i);
  if (acceptedEntity) {
    return `New ${readableEntity(acceptedEntity[1])}`;
  }
  const assignment = withoutAnchorPrefix.match(/^([a-z0-9_]+)\s+([a-z0-9_]+)\s*=\s*(.+)$/i);
  if (assignment) {
    return `${readableLabel(assignment[2])}: ${readableFactValue(assignment[3])}`;
  }
  const stateChange = withoutAnchorPrefix.match(/^([a-z0-9_]+)\s*->\s*(.+)$/i);
  if (stateChange) {
    return `${readableLabel(stateChange[1])}: ${readableFactValue(stateChange[2])}`;
  }
  const fact = withoutAnchorPrefix.match(/^([a-z0-9_]+):\s*(.+)$/i);
  if (fact) {
    return `${readableLabel(fact[1])}: ${readableFactValue(fact[2])}`;
  }
  const stateChangeId = withoutAnchorPrefix.match(/^state_fact_(.+)$/i);
  if (stateChangeId) {
    return `State change: ${readableValue(stateChangeId[1])}`;
  }
  const relationship = readableRelationship(withoutAnchorPrefix);
  return relationship ?? readableFreeText(withoutAnchorPrefix);
}

export function readablePromptText(
  section: { items: string[] },
  options: { maxItems?: number } = {},
): string {
  const items = readablePromptItems(section);
  if (items.length === 0) {
    return "Unknown.";
  }
  const visibleItems = options.maxItems ? items.slice(0, options.maxItems) : items;
  const overflow =
    options.maxItems && items.length > options.maxItems
      ? `\n\n${items.length - options.maxItems} more canon details available.`
      : "";
  return `${visibleItems.map(toSentence).join("\n\n")}${overflow}`;
}

export function readablePromptSummary(section: { items: string[] }): string {
  const items = readablePromptItems(section);
  if (items.length === 0) {
    return "No prompt details available.";
  }
  const label = items.length === 1 ? "prompt detail" : "prompt details";
  return `${items.length.toLocaleString()} ${label} ready.`;
}

function readablePromptItems(section: { items: string[] }): string[] {
  return readableOutputItems(section.items)
    .filter((item) => !/^Scene ID:/iu.test(item));
}

export function readableOutputText(value: string): string {
  if (isInternalOutputPlaceholder(value)) {
    return "Unknown";
  }
  return readableOutputItem(value) || "Unknown";
}

export function isInternalOutputPlaceholder(value: string): boolean {
  return value.trim() === SOURCE_BACKED_PLACEHOLDER;
}

function toSentence(value: string): string {
  const trimmed = value.trim();
  if (/[\d).!?]$/u.test(trimmed)) {
    return trimmed;
  }
  return `${trimmed}.`;
}

function readableEntity(value: string): string {
  const kindMatch = value.match(
    /^(character|entity|location|organization|building|item|skill|vehicle)_(.+)$/i,
  );
  if (!kindMatch) {
    return readableValue(value);
  }
  const [, kind, name] = kindMatch;
  if (/^\d+$/u.test(name)) {
    return readableLabel(kind);
  }
  return `${readableLabel(kind)}: ${readableValue(name)}`;
}

function readableFreeText(value: string): string {
  if (/[ _]/u.test(value) && /_/u.test(value)) {
    return readableValue(value);
  }
  return fixApostropheCapitalization(value);
}

function readableRelationship(value: string): string | null {
  const match = value.match(/^([a-z0-9_]+)\s+([a-z0-9_]+)\s+([a-z0-9_]+)$/i);
  if (!match) {
    return null;
  }
  const [, source, relationship, target] = match;
  return `${readableValue(source)} ${readableLabel(relationship).toLowerCase()} ${readableValue(target)}`;
}

function readableLabel(value: string): string {
  const labelOverrides: Record<string, string> = {
    display_name: "Name",
    under_entity: "under",
    bound_to_system: "bound to",
    owns_vehicle: "owns",
    member_of: "member of",
    has_item: "has",
  };
  const normalizedValue = value.toLowerCase();
  if (labelOverrides[normalizedValue]) {
    return labelOverrides[normalizedValue];
  }
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace(/'([A-Z])/g, (_, character: string) => `'${character.toLowerCase()}`);
}

function readableValue(value: string): string {
  return value
    .replace(/\b(entity|character|location|organization|building|item|skill|vehicle)_/gi, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase())
    .replace(/'([A-Z])/g, (_, character: string) => `'${character.toLowerCase()}`);
}

function readableFactValue(value: string): string {
  const trimmed = value.trim();
  if (/_/u.test(trimmed) || /^[a-z]+$/u.test(trimmed)) {
    return readableValue(trimmed);
  }
  if (/^[a-z]+(?:\s+[a-z]+){0,3}$/u.test(trimmed)) {
    return readableValue(trimmed);
  }
  return fixApostropheCapitalization(trimmed);
}

function fixApostropheCapitalization(value: string): string {
  return value.replace(/'([A-Z])/g, (_, character: string) => `'${character.toLowerCase()}`);
}
