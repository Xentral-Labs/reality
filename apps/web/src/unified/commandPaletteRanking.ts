export function normalizeSearch(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replaceAll("ß", "ss")
    .replaceAll("æ", "ae")
    .replaceAll("œ", "oe");
}
function words(value: string): string[] {
  return normalizeSearch(value).match(/[\p{L}\p{N}]+/gu) || [];
}
function editOne(left: string, right: string): boolean {
  const a = [...left],
    b = [...right];
  if (Math.abs(a.length - b.length) > 1) return false;
  let i = 0;
  while (i < Math.min(a.length, b.length) && a[i] === b[i]) i++;
  const tail = (value: string[], start: number) => value.slice(start).join("");
  if (a.length === b.length)
    return (
      tail(a, i + 1) === tail(b, i + 1) ||
      (i + 1 < a.length &&
        a[i] === b[i + 1] &&
        a[i + 1] === b[i] &&
        tail(a, i + 2) === tail(b, i + 2))
    );
  return a.length > b.length ? tail(a, i + 1) === tail(b, i) : tail(a, i) === tail(b, i + 1);
}
export function matchTier(query: string, labels: string[], references: string[]): number | null {
  query = query.trim();
  if (!query) return null;
  if (references.includes(query)) return 0;
  const folded = normalizeSearch(query);
  const names = labels.map(normalizeSearch),
    refs = references.map(normalizeSearch);
  if ([...names, ...refs].includes(folded)) return 1;
  const tokens = words(query),
    nameWords = names.flatMap(words);
  if (
    refs.some((ref) => ref.startsWith(folded)) ||
    (tokens.length && tokens.every((token) => nameWords.some((word) => word.startsWith(token))))
  )
    return 2;
  if (
    tokens.length &&
    tokens.every((token) =>
      nameWords.some(
        (word) => word.startsWith(token) || ([...token].length >= 5 && editOne(token, word)),
      ),
    )
  )
    return 3;
  return null;
}

export type RankedPaletteValue = {
  key: string;
  label: string;
  tier: number;
  group: string;
  sortKey?: [number, number, number, number, string, string, string];
};
/** The same tuple as SQL, including byte-independent Unicode codepoint ordering. */
export function comparePaletteEntries(a: RankedPaletteValue, b: RankedPaletteValue): number {
  const key = (entry: RankedPaletteValue) =>
    entry.sortKey || [
      entry.tier,
      1,
      1,
      entry.group === "reports"
        ? 18
        : entry.group === "actions"
          ? 19
          : entry.group === "pages"
            ? 20
            : entry.group === "help"
              ? 21
              : 22,
      normalizeSearch(entry.label),
      entry.key.split(":")[0],
      entry.key.slice(entry.key.indexOf(":") + 1),
    ];
  const left = key(a),
    right = key(b);
  for (let i = 0; i < left.length; i++) {
    if (typeof left[i] === "number" && typeof right[i] === "number") {
      const delta = Number(left[i]) - Number(right[i]);
      if (delta) return delta;
    } else {
      const l = [...String(left[i])],
        r = [...String(right[i])];
      for (let j = 0; j < Math.min(l.length, r.length); j++) {
        const delta = l[j].codePointAt(0)! - r[j].codePointAt(0)!;
        if (delta) return delta;
      }
      if (l.length !== r.length) return l.length - r.length;
    }
  }
  return 0;
}
export function palettePreview<T extends { key: string; group: string }>(ranked: T[]): T[] {
  const seen = new Set<string>(),
    counts = new Map<string, number>();
  return ranked
    .filter((entry) => {
      if (seen.has(entry.key)) return false;
      seen.add(entry.key);
      const count = counts.get(entry.group) || 0;
      counts.set(entry.group, count + 1);
      return count < 4;
    })
    .slice(0, 12);
}
