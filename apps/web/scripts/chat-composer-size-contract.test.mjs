import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const composer = fs.readFileSync(path.join(root, "src", "unified", "ChatComposer.tsx"), "utf8");
const styles = fs.readFileSync(path.join(root, "src", "tailwind.css"), "utf8");

test("the composer starts compact and grows with its content", () => {
  assert.match(styles, /\.reality-chat-composer textarea \{[\s\S]*min-height: 44px/u);
  assert.match(styles, /\.reality-chat-composer textarea \{[\s\S]*max-height: 200px/u);
  assert.match(styles, /\.reality-chat-composer textarea \{[\s\S]*resize: none/u);
  assert.match(composer, /Math\.min\(node\.scrollHeight, 200\)/u);
});
