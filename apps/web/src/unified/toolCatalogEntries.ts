import type { ToolCapability } from "../api";

export const capabilityTitle = (
  row: ToolCapability,
  translate: (value: string) => string,
  language: string,
) => row.labels[language] || translate(row.title);

export function filterCapabilities(
  rows: ToolCapability[],
  query: string,
  topic: string,
  purpose: string,
  translate: (value: string) => string,
  language: string,
): ToolCapability[] {
  const needle = query.trim().toLocaleLowerCase();
  return rows.filter(
    (row) =>
      (!topic || row.topic === topic) &&
      (!purpose || row.purpose === purpose) &&
      [
        capabilityTitle(row, translate, language),
        row.title,
        translate(row.description),
        ...row.commands,
        ...row.mcp,
        ...(row.views || []),
        ...(row.projections || []),
        ...(row.actions || []),
        ...(row.discovery || []),
      ]
        .join(" ")
        .toLocaleLowerCase()
        .includes(needle),
  );
}
