import type { GraphNode } from "../../api";

/** Keep discovery vocabulary supplied by the same model that executes the query. */
export function catalogGroups(nodes: GraphNode[], search = ""): [string, GraphNode[]][] {
  const query = search.trim().toLocaleLowerCase();
  const groups = new Map<string, GraphNode[]>();
  for (const node of nodes) {
    const words = [
      node.label,
      node.key,
      node.category ?? "",
      ...(node.aliases ?? []),
      ...node.properties.flatMap((field) => [field.label, field.key]),
    ]
      .join(" ")
      .toLocaleLowerCase();
    if (!words.includes(query)) continue;
    const category = node.category ?? "";
    groups.set(category, [...(groups.get(category) ?? []), node]);
  }
  return [...groups];
}
