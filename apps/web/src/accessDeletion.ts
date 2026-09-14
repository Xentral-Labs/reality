// Client-side mirror of the applicant deletion guards (spec 192). The server stays the
// authority (reality.services.account_deletion.delete_account); these rules only decide
// whether a control is offered and whether the confirm button is enabled.
import type { DeletionPreview } from "./api";

export type { DeletionPreview };

/**
 * Compared as a constant by the server (`account_deletion.CONFIRMATION_WORD`) and
 * displayed literally in every UI language. Declared here rather than imported so
 * this module stays type-only in its imports and can be unit-tested directly;
 * `access-deletion.test.mjs` asserts it still equals the company danger zone's word.
 */
export const DELETE_CONFIRMATION_WORD = "DELETE";

/** Sign-in normalizes an address the same way, so the confirmation may differ in case. */
const normalizeEmail = (value: string): string => value.trim().toLowerCase();

export const deletionConfirmationValid = (
  email: string,
  typedEmail: string,
  typedWord: string,
): boolean =>
  normalizeEmail(typedEmail) === normalizeEmail(email) &&
  normalizeEmail(email).length > 0 &&
  typedWord === DELETE_CONFIRMATION_WORD;

type RowShape = { id: string; email: string; is_platform_admin?: boolean };

/**
 * An administrator never deletes their own account, and never another administrator's.
 * The server refuses both; hiding the control keeps the list honest about what it offers.
 */
export const deletionOffered = (row: RowShape, actor: RowShape): boolean =>
  row.id !== actor.id && !row.is_platform_admin;
