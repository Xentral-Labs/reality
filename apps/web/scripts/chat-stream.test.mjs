import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import ts from "typescript";
const source = await readFile(new URL("../src/chatStream.ts", import.meta.url), "utf8");
const js = ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 },
}).outputText;
const { readChatStream } = await import(
  "data:text/javascript;base64," + Buffer.from(js).toString("base64")
);
const bytes = (text) => new TextEncoder().encode(text);
function response(chunks) {
  return new Response(
    new ReadableStream({
      start(controller) {
        for (const c of chunks) controller.enqueue(c);
        controller.close();
      },
    }),
  );
}
test("split UTF-8, provisional resets and final recorded IDs", async () => {
  const done = {
    type: "done",
    user: { id: "u", content: "Question" },
    assistant: { id: "a", content: "Grüße" },
  };
  const raw = bytes(
    [
      { type: "start" },
      { type: "delta", text: "Looking" },
      { type: "reset" },
      { type: "delta", text: "Grüße" },
      done,
    ]
      .map(JSON.stringify)
      .join("\n") + "\n",
  );
  const events = [];
  const result = await readChatStream(response([...raw].map((v) => new Uint8Array([v]))), (e) =>
    events.push(e),
  );
  assert.equal(result.assistant.id, "a");
  assert.equal(events.filter((e) => e.type === "delta").at(-1).text, "Grüße");
});
test("truncation and explicit errors never succeed or retry", async () => {
  await assert.rejects(
    readChatStream(response([bytes('{"type":"delta","text":"partial"}\n')]), () => {}),
    /incomplete/,
  );
  await assert.rejects(
    readChatStream(response([bytes('{"type":"error","message":"Denied"}\n')]), () => {}),
    /Denied/,
  );
});
test("text is delivered before server completion", async () => {
  let controller;
  const stream = new ReadableStream({
    start(c) {
      controller = c;
    },
  });
  let visible = "";
  let completed = false;
  const pending = readChatStream(new Response(stream), (e) => {
    if (e.type === "delta") visible += e.text;
  }).then((v) => {
    completed = true;
    return v;
  });
  controller.enqueue(bytes('{"type":"delta","text":"Early"}\n'));
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(visible, "Early");
  assert.equal(completed, false);
  controller.enqueue(
    bytes(
      '{"type":"done","user":{"id":"u","content":"q"},"assistant":{"id":"a","content":"Early"}}\n',
    ),
  );
  controller.close();
  await pending;
});
