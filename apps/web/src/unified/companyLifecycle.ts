// Client-side mirror of the company and sandbox lifecycle guards. The server stays the
// authority (reality.services.core.archive_tenant / permanently_delete_tenant and
// reality.services.playground.archive_run / restore_run); these rules only explain a
// disabled control before the request is made.
import type { CompanyRow, SandboxRun, Tenant } from "../api";

/** Compared as a constant by the server; displayed literally in every UI language. */
export const DELETE_CONFIRMATION_WORD = "DELETE";

/** A business company has the tenant lifecycle; a sandbox or demo company has the run lifecycle. */
export type LifecycleKind = "company" | "sandbox";

export type ArchiveGuardReason = "not-owner" | "last-active" | "unavailable";
export type ArchiveGuard =
  | { allowed: true; kind: LifecycleKind }
  | { allowed: false; kind: LifecycleKind; reason: ArchiveGuardReason };

type CompanyShape = Pick<Tenant, "purpose" | "sandbox_run_id" | "company_kind">;

/** Sandboxes and demo companies belong to their playground run, not to the tenant lifecycle. */
export const isPracticeCompany = (company: CompanyShape): boolean =>
  company.purpose === "playground" ||
  !!company.sandbox_run_id ||
  company.company_kind === "sandbox" ||
  company.company_kind === "demo";

export const lifecycleKind = (company: CompanyShape): LifecycleKind =>
  isPracticeCompany(company) ? "sandbox" : "company";

export function archiveGuard(company: Tenant, companies: Tenant[]): ArchiveGuard {
  const kind = lifecycleKind(company);
  if (company.role !== "owner") return { allowed: false, kind, reason: "not-owner" };
  if (kind === "sandbox") {
    if (!company.sandbox_run_id) return { allowed: false, kind, reason: "unavailable" };
    // Archiving the only entry would leave the switcher empty.
    if (companies.length <= 1) return { allowed: false, kind, reason: "last-active" };
    return { allowed: true, kind };
  }
  const active = companies.filter((row) => !isPracticeCompany(row)).length;
  if (active <= 1) return { allowed: false, kind, reason: "last-active" };
  return { allowed: true, kind };
}

export const ARCHIVE_GUARD_MESSAGES: Record<ArchiveGuardReason, string> = {
  "not-owner": "Only company owners can archive this company.",
  "last-active": "This is your last active company. Create or restore another company first.",
  unavailable: "This sandbox cannot be archived from here.",
};

const newestFirst = (a: string | null | undefined, b: string | null | undefined) =>
  (a ?? "") < (b ?? "") ? 1 : (a ?? "") > (b ?? "") ? -1 : 0;

/** Archived business companies, most recently archived first. */
export const archivedCompanies = (rows: CompanyRow[]): CompanyRow[] =>
  rows
    .filter((row) => !!row.archived_at && !isPracticeCompany(row))
    .sort((a, b) => newestFirst(a.archived_at, b.archived_at));

/** Archived sandbox runs, most recently archived first. */
export const archivedSandboxes = (runs: SandboxRun[]): SandboxRun[] =>
  runs
    .filter((run) => run.status === "archived")
    .sort((a, b) => newestFirst(a.archived_at, b.archived_at));

export const deleteConfirmationValid = (
  company: Pick<CompanyRow, "name">,
  name: string,
  word: string,
): boolean => name === company.name && word === DELETE_CONFIRMATION_WORD;

export type LossSummary = Array<{ label: string; count: number }>;

/** What a permanent deletion removes, in the words the companies endpoint already uses. */
export const lossSummary = (
  row: Pick<CompanyRow, "source_count" | "evidence_count" | "reality_count">,
): LossSummary => [
  { label: "Sources", count: row.source_count },
  { label: "Evidence documents", count: row.evidence_count },
  { label: "Reality records", count: row.reality_count },
];
