// A minimal, complete Inspector read. Row previews open an inline Inspector, and an
// incomplete shape (the generic register fallback) crashes the page.
export const isInspectorRead = (path) => /\/inspector\/[^/]+\/[^/]+$/.test(path);
export function inspectorRecord(path, title = "Record") {
  const [, kind, id] = path.match(/\/inspector\/([^/]+)\/([^/]+)$/) || [];
  return {
    kind: kind || "document",
    id: id || "record",
    eyebrow: "",
    title,
    subtitle: "",
    status: "",
    meaning: "",
    business_reference: null,
    guidance: null,
    technical_rows: [],
    metrics: [],
    trail: [],
    sections: [],
    events: [],
    source_payload: null,
    evidence_lines: [],
  };
}
