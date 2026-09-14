import assert from "node:assert/strict";
import test from "node:test";
import {
  DELETE_CONFIRMATION_WORD,
  deletionConfirmationValid,
  deletionOffered,
} from "../src/accessDeletion.ts";
import { DELETE_CONFIRMATION_WORD as COMPANY_WORD } from "../src/unified/companyLifecycle.ts";

const admin = { id: "usr_admin", email: "owner@reality.local", is_platform_admin: true };
const applicant = { id: "usr_free", email: "free5@example.com", is_platform_admin: false };

test("both answers must be right before the confirm button is enabled", () => {
  assert.equal(deletionConfirmationValid(applicant.email, "free5@example.com", "DELETE"), true);
  assert.equal(deletionConfirmationValid(applicant.email, "free5@example.com", ""), false);
  assert.equal(deletionConfirmationValid(applicant.email, "", "DELETE"), false);
  assert.equal(deletionConfirmationValid(applicant.email, "other@example.com", "DELETE"), false);
});

test("the confirmation word is compared as a constant, never translated", () => {
  assert.equal(DELETE_CONFIRMATION_WORD, "DELETE");
  // One vocabulary across both danger zones, and the same constant the server compares.
  assert.equal(DELETE_CONFIRMATION_WORD, COMPANY_WORD);
  for (const word of ["delete", "Delete", "LÖSCHEN", "ELIMINAR", " DELETE"]) {
    assert.equal(deletionConfirmationValid(applicant.email, applicant.email, word), false, word);
  }
});

test("the address is compared the way sign-in normalizes it", () => {
  for (const typed of ["Free5@Example.com", "  free5@example.com  ", "FREE5@EXAMPLE.COM"]) {
    assert.equal(deletionConfirmationValid(applicant.email, typed, "DELETE"), true, typed);
  }
});

test("an empty address never confirms, whatever is typed", () => {
  assert.equal(deletionConfirmationValid("", "", "DELETE"), false);
  assert.equal(deletionConfirmationValid("", "   ", "DELETE"), false);
});

test("the control is withheld for the acting administrator and for administrators", () => {
  assert.equal(deletionOffered(applicant, admin), true);
  assert.equal(deletionOffered(admin, admin), false);
  assert.equal(deletionOffered({ ...applicant, is_platform_admin: true }, admin), false);
});
