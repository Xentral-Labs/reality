export type TraceSide = "left" | "right";
export type TraceNode = { x: number; y: number; side: TraceSide };

const ORIGIN_KINDS = new Set([
  "party",
  "item",
  "location",
  "source_record",
  "document",
  "document_line",
]);

export function connectionTraceLayout(kinds: string[], availableWidth: number) {
  const width = Math.max(660, availableWidth);
  const nodeWidth = 172;
  const nodeHeight = 58;
  const leftCount = kinds.filter((kind) => ORIGIN_KINDS.has(kind)).length;
  const rightCount = kinds.length - leftCount;
  const height = Math.max(440, Math.max(leftCount, rightCount) * 74 + 74);
  const root = { x: (width - nodeWidth) / 2, y: (height - nodeHeight) / 2 };
  let leftIndex = 0;
  let rightIndex = 0;
  const position = (index: number, total: number) =>
    (height - total * nodeHeight - (total - 1) * 16) / 2 + index * (nodeHeight + 16);
  const nodes: TraceNode[] = kinds.map((kind) => {
    const side: TraceSide = ORIGIN_KINDS.has(kind) ? "left" : "right";
    const index = side === "left" ? leftIndex++ : rightIndex++;
    const total = side === "left" ? leftCount : rightCount;
    return {
      side,
      x: side === "left" ? 24 : width - nodeWidth - 24,
      y: position(index, total),
    };
  });
  return { width, height, nodeWidth, nodeHeight, root, nodes };
}
