export function mergeWorkRows<T extends { id: string }>(previous: T[], incoming: T[]): T[] {
  const rows = new Map(previous.map((row) => [row.id, row]));
  for (const row of incoming) rows.set(row.id, row);
  return [...rows.values()];
}
