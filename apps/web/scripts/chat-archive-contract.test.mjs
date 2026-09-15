import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const chat = fs.readFileSync(path.join(root, "src", "unified", "ChatPage.tsx"), "utf8");

test("the unified conversation list preserves archive and restore controls", () => {
  assert.match(chat, /api\.deleteCopilotSession\(selection\.tenant, row\.id\)/u);
  assert.match(chat, /api\.restoreCopilotSession\(selection\.tenant, row\.id\)/u);
  assert.match(chat, /data-chat-session-archive/u);
  assert.match(chat, /data-chat-session-restore/u);
  assert.match(chat, /data\.has_archived/u);
});

test("archived conversations use the retained archive read and remain read-only", () => {
  assert.match(chat, /api\.copilot\([\s\S]*showArchived/u);
  assert.match(chat, /api\.copilot\(selection\.tenant, selection\.session, showArchived\)/u);
  assert.match(chat, /onClick=\{\(\) => selectSession\(row\.id\)\}/u);
  assert.match(chat, /showArchived \? \([\s\S]*Archived — read only/u);
  assert.match(chat, /Back to chats/u);
});
