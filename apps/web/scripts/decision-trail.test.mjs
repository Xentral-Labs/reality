import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { decisionHref, deciderSentence, fillSentence } from "../src/unified/decisionTrail.ts";

const source = (path) => readFileSync(new URL(`../src/unified/${path}`, import.meta.url), "utf8");

const token = (issuer) => ({
  kind: "mcp_token",
  token_name: "Claude Desktop",
  token_prefix: "ros_mcp_abc",
  revoked: false,
  issuer,
});

test("a person, a token and nobody read as three different sentences", () => {
  const person = deciderSentence("executed", { kind: "person", name: "Anna" });
  const viaToken = deciderSentence("executed", token("Olga"));
  const legacy = deciderSentence("executed", token(null));
  const nobody = deciderSentence("executed", { kind: "unknown" });

  assert.equal(fillSentence(person.template, person.values), "Confirmed by Anna");
  assert.equal(
    fillSentence(viaToken.template, viaToken.values),
    "Confirmed through token Claude Desktop, issued by Olga",
  );
  assert.equal(
    fillSentence(legacy.template, legacy.values),
    "Confirmed through token Claude Desktop, issuer unknown",
  );
  assert.equal(nobody.template, "Confirmed, decided by an unrecorded person");
  // The issuer answers for the token and is never presented as the one who confirmed.
  assert.doesNotMatch(viaToken.template, /Confirmed by/);
});

test("a rejection is attributed like an approval, and a pending one is undecided", () => {
  assert.equal(
    deciderSentence("rejected", { kind: "person", name: "Anna" }).template,
    "Rejected by {name}",
  );
  assert.equal(
    deciderSentence("rejected", token("Olga")).template,
    "Rejected through token {token}, issued by {issuer}",
  );
  assert.equal(deciderSentence("proposed", { kind: "unknown" }).template, "Not decided yet");
});

test("a decision link opens that decision on the history tab of its company", () => {
  assert.equal(
    decisionHref("ten_1", "act_2"),
    "/app/decisions?tenant=ten_1&decisions_view=history&proposal=act_2",
  );
});

test("the decisions page offers pending and history as tabs over the same register", () => {
  const page = source("DecisionsPage.tsx");
  const routing = source("routing.ts");

  assert.match(page, /api\.changeProposals\(tenant, view, page, query, size, tool\)/);
  assert.match(page, /history \? 25 : 50/);
  assert.match(page, /aria-pressed=\{view === "pending"\}/);
  assert.match(page, /aria-pressed=\{view === "history"\}/);
  assert.match(page, /<DecisionLine/);
  assert.match(routing, /decisions_view/);
  assert.match(routing, /decisionsView/);
});

test("a settled decision opened by link states who settled it", () => {
  const card = source("ProposalReviewCard.tsx");
  assert.match(card, /<DecisionLine/);
});

test("the decision line renders the server's attribution and translates it", () => {
  const line = source("DecisionLine.tsx");
  assert.match(line, /deciderSentence\(/);
  assert.match(line, /t\(sentence\.template\)/);
  assert.match(line, /decisionHref\(/);
  assert.match(line, /Token revoked/);
});

test("a record created here names the decision behind it and links to it", () => {
  const badge = source("SourceBadge.tsx");
  assert.match(badge, /<DecisionLine/);
  assert.match(badge, /origin\.decision/);
  assert.match(source("MasterDataPage.tsx"), /<SourceBadge[^>]*tenant=\{tenant\}/);
  assert.match(source("OrdersPage.tsx"), /<SourceBadge[^>]*tenant=\{tenant\}/);
});

test("an activity states its decision instead of a bare identifier", () => {
  const drawer = source("ActivityDrawer.tsx");
  const statements = drawer.match(/event\.decision && \(/g) || [];
  // Both the list and the table presentation carry the decision line.
  assert.equal(statements.length, 2);
  assert.match(drawer, /<DecisionLine decision=\{event\.decision\} tenant=\{tenant\}/);
});
