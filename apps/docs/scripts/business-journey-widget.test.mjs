import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const widget = fs.readFileSync(
  new URL("../public/journey-guide-widget/widget.js", import.meta.url),
  "utf8",
);

test("public widget is closed by default and exposes an accessible dialog", () => {
  assert.match(widget, /aria-haspopup="dialog"/u);
  assert.match(widget, /aria-expanded="false"/u);
  assert.match(widget, /role="dialog"/u);
  assert.match(widget, /data-open="false"/u);
  assert.match(widget, /event\.key === "Escape"/u);
});

test("public widget asks only the public guide endpoint and keeps failure bounded", () => {
  assert.match(widget, /\/api\/journey-guide\/questions/u);
  assert.match(widget, /controller\.abort\(\)/u);
  assert.match(widget, /journey question unavailable/u);
  assert.doesNotMatch(widget, /localStorage|sessionStorage|document\.cookie/u);
  assert.doesNotMatch(widget, /tenant_id|company_id|Authorization/u);
});

test("public widget provides localized capability copy and guide citations", () => {
  assert.match(widget, /Stelle eine Frage zu Reality/u);
  assert.match(widget, /Ask a question about Reality/u);
  assert.match(widget, /Stel een vraag over Reality/u);
  assert.match(widget, /Haz una pregunta sobre Reality/u);
  assert.match(widget, /locale: apiLocale/u);
  assert.match(widget, /encodeURIComponent\(id\)/u);
  assert.match(widget, /This public chat cannot see company data/u);
});

test("guide citations preserve the chat and open details in a new tab", () => {
  assert.match(widget, /link\.target = "_blank"/u);
  assert.match(widget, /link\.rel = "noopener noreferrer"/u);
  assert.match(widget, /Open journey .* in a new tab/u);
});

test("widget uses a readable desktop panel and mobile bottom sheet", () => {
  assert.match(widget, /grid-template-rows:auto minmax\(0,1fr\) auto/u);
  assert.match(widget, /\.conversation\{[^}]*overflow-y:auto/u);
  assert.match(widget, /width:min\(640px,calc\(100vw - 48px\)\)/u);
  assert.match(widget, /bottom:24px;[^}]*height:calc\(100dvh - 48px\)/u);
  assert.doesNotMatch(widget, /height:min\(720px,calc\(100vh - 120px\)\)/u);
  assert.match(widget, /@media\(max-width:700px\)/u);
  assert.match(widget, /border-radius:24px 24px 0 0/u);
});

test("widget keeps ephemeral turns and renders provider text without HTML injection", () => {
  assert.match(widget, /appendUserMessage/u);
  assert.match(widget, /appendFormattedText/u);
  assert.match(widget, /document\.createTextNode/u);
  assert.doesNotMatch(widget, /innerHTML\s*=\s*answer/u);
  assert.doesNotMatch(widget, /localStorage|sessionStorage|document\.cookie/u);
});

test("widget resends bounded in-memory turns for coherent follow-up questions", () => {
  assert.match(widget, /this\.history = \[\]/u);
  assert.match(widget, /history: this\.history/u);
  assert.match(widget, /this\.history\.push/u);
  assert.match(widget, /this\.history = this\.history\.slice\(-6\)/u);
  assert.doesNotMatch(widget, /localStorage|sessionStorage|document\.cookie/u);
});

test("empty chat offers localized examples and citations explain journey IDs", () => {
  assert.match(widget, /examplesTitle/u);
  assert.match(widget, /Wie bilde ich einen B2B-Auftrag ab/u);
  assert.match(widget, /example-list button/u);
  assert.match(widget, /this\.form\.requestSubmit\(\)/u);
  assert.match(widget, /this\.examples\?\.remove\(\)/u);
  assert.match(widget, /answer\.matches/u);
  assert.match(widget, /citation-title/u);
  assert.match(widget, /matches\.get\(id\)\?\.title/u);
});

test("answers render readable headings, paragraphs and bullet lists safely", () => {
  assert.match(widget, /section-title/u);
  assert.match(widget, /document\.createElement\("h3"\)/u);
  assert.match(widget, /document\.createElement\("ul"\)/u);
  assert.match(widget, /document\.createElement\("li"\)/u);
  assert.match(widget, /So geht/u);
  assert.doesNotMatch(widget, /container\.innerHTML/u);
});

test("new answers open at their beginning instead of forcing the reader to the end", () => {
  assert.match(widget, /scrollAnswerToStart\(box\)/u);
  assert.match(widget, /box\.offsetTop - this\.conversation\.offsetTop/u);
  assert.doesNotMatch(widget, /this\.conversation\.append\(box\);\s*this\.scrollConversation\(\)/u);
});

test("example submission gives immediate modern loading feedback", () => {
  assert.match(widget, /this\.shadowRoot\.querySelectorAll\("\.example-list button"\)/u);
  assert.doesNotMatch(widget, /connectedCallback\(\)\s*\{[\s\S]*?\broot\.querySelectorAll/u);
  assert.match(widget, /pending\.setAttribute\("role", "status"\)/u);
  assert.match(widget, /typing-dots/u);
  assert.match(widget, /pending\.setAttribute\("aria-label", copy\.wait\)/u);
  assert.doesNotMatch(widget, /pending-mark|pending-copy/u);
  assert.match(widget, /@keyframes rjc-pulse/u);
  assert.match(widget, /prefers-reduced-motion/u);
  assert.match(widget, /this\.examples\?\.remove\(\)/u);
});

test("citations use a compact accessible table instead of large badges", () => {
  assert.match(widget, /document\.createElement\("table"\)/u);
  assert.match(widget, /document\.createElement\("tbody"\)/u);
  assert.match(widget, /document\.createElement\("tr"\)/u);
  assert.match(widget, /citation-open/u);
  assert.match(widget, /table-layout:fixed/u);
  assert.doesNotMatch(widget, /citations a::after/u);
});
