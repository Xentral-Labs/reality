// Spec 182 FR-006, T020: the Storyline destination round-trips through routing and
// the product boundary stays intact (no `playground` surface returns).
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";
import ts from "typescript";

const load = async (relative) => {
  const source = readFileSync(new URL(`../src/${relative}`, import.meta.url), "utf8")
    // Data URLs cannot resolve relative modules; the helpers only need the language.
    .replace(
      /import \{ currentLanguage \} from "\.\.\/localization";/,
      'const currentLanguage = () => "en";',
    )
    .replace(/import type [^;]+;/g, "");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`);
};

test("the storyline destination round-trips with its chapter and drops unknown params", async () => {
  const { readSelection, selectionUrl, unifiedPath, companySelection } =
    await load("unified/routing.ts");
  assert.equal(unifiedPath("/app/storyline"), true);
  const selection = readSelection(
    new URL("http://x/app/storyline?tenant=company&chapter=explain-hold&token=secret"),
  );
  assert.equal(selection.route, "storyline");
  assert.equal(selection.storylineChapter, "explain-hold");
  assert.equal(selectionUrl(selection), "/app/storyline?tenant=company&chapter=explain-hold");
  assert.equal(
    readSelection(new URL("http://x/app/storyline?chapter=%3Cscript%3E")).storylineChapter,
    "",
  );
  assert.equal(companySelection(selection, "other").storylineChapter, "");
  assert.equal(selectionUrl(companySelection(selection, "other")), "/app/storyline?tenant=other");
  // Free play is a browser-only mode carried in the chapter slot (FR-011, analysis M9).
  assert.equal(
    readSelection(new URL("http://x/app/storyline?tenant=company&chapter=free")).storylineChapter,
    "free",
  );
});

test("presentation mode derives its next move from the page and takes the default branch", async () => {
  const { nextPresentationAction, PRESENTATION_BEATS } = await load("unified/storylineState.ts");
  const chapter = (branches = []) => ({ key: "dispatch", branches });
  const detail = (over) => ({ chapter: chapter(), can_run: true, preconditions: [], ...over });
  const at = (input) =>
    nextPresentationAction({
      currentChapter: "dispatch",
      chosenBranch: null,
      busy: false,
      ...input,
    });
  assert.equal(at({ detail: null, step: null }), null);
  assert.equal(at({ detail: detail(), step: null, busy: true }), null);
  assert.deepEqual(at({ detail: detail(), step: null }), { kind: "prepare" });
  assert.deepEqual(at({ detail: detail({ can_run: false }), step: null }), {
    kind: "end",
    reason: "blocked",
  });
  assert.deepEqual(at({ detail: detail(), step: { status: "pending", review: {} } }), {
    kind: "confirm",
  });
  assert.deepEqual(
    at({
      detail: detail(),
      step: { status: "pending", review: null, error: { unresolved: true } },
    }),
    { kind: "end", reason: "unresolved" },
  );
  const branches = [
    { key: "call", default: false },
    { key: "explain", default: true },
  ];
  assert.deepEqual(
    at({ detail: detail({ chapter: chapter(branches) }), step: { status: "refused" } }),
    { kind: "branch", branch: "explain" },
  );
  assert.deepEqual(
    at({
      detail: detail({ chapter: chapter(branches) }),
      step: { status: "done" },
      chosenBranch: "call",
      currentChapter: "call-customer",
    }),
    { kind: "next", chapter: "call-customer" },
  );
  assert.deepEqual(at({ detail: detail(), step: { status: "done" }, currentChapter: null }), {
    kind: "end",
    reason: "finished",
  });
  assert.deepEqual(at({ detail: detail(), step: null, currentChapter: "ship" }), {
    kind: "next",
    chapter: "ship",
  });
  assert.ok(PRESENTATION_BEATS.next > PRESENTATION_BEATS.confirm, "the explanation gets read");
});

test("free play is a page mode, never a server flag, and restart is offered where a chapter is blocked", async () => {
  const { FREE_PLAY } = await load("unified/storylineState.ts");
  assert.equal(FREE_PLAY, "free");
  const unified = new URL("../src/unified/", import.meta.url);
  const page = readFileSync(new URL("StorylinePage.tsx", unified), "utf8");
  const narrator = readFileSync(new URL("StorylineNarrator.tsx", unified), "utf8");
  assert.match(page, /storylineApi\s*\.freeTrace\(/, "free play reads the trace outside chapters");
  assert.match(page, /storylineApi\s*\.deltaAt\(/, "a picked confirmation loads its own delta");
  assert.doesNotMatch(
    page,
    /free_play|freePlay:\s*true/,
    "no free-play flag is sent to the server",
  );
  assert.match(narrator, /data-storyline-missing/);
  assert.match(narrator, /data-storyline-action="restart"/);
  assert.match(narrator, /data-storyline-action="free-play"/);
});

test("the entry routing knows the destination and keeps the old playground retired", async () => {
  const { resolveEntry } = await load("entryRouting.ts").catch(() => ({}));
  const source = readFileSync(new URL("../src/entryRouting.ts", import.meta.url), "utf8");
  assert.match(source, /"storyline",/);
  assert.match(source, /playground/);
  if (resolveEntry) assert.equal(resolveEntry(new URL("http://x/playground")).kind, "retired");
});

test("the storyline surface lives under unified and never as a playground page", () => {
  const unified = new URL("../src/unified/", import.meta.url);
  for (const name of [
    "StorylinePage.tsx",
    "StorylineNarrator.tsx",
    "StorylineStage.tsx",
    "StorylineProtocol.tsx",
    "storylineState.ts",
  ])
    assert.ok(existsSync(new URL(name, unified)), `${name} exists`);
  assert.equal(existsSync(new URL("../src/playground", import.meta.url)), false);
  const page = readFileSync(new URL("StorylinePage.tsx", unified), "utf8");
  assert.match(page, /storylineApi\.confirm\(/, "confirm goes through the storyline route");
  assert.doesNotMatch(page, /ActionCard/, "the ordinary action card is not used to confirm");
});

test("storyline state helpers derive the phase from the latest step only", async () => {
  const { phaseOf, compareFindings, rowIsNew } = await load("unified/storylineState.ts");
  assert.equal(phaseOf(null), "idle");
  assert.equal(phaseOf({ status: "done" }), "done");
  assert.equal(phaseOf({ status: "refused" }), "refused");
  assert.equal(phaseOf({ status: "rejected" }), "idle");
  assert.equal(phaseOf({ status: "pending", review: { tool: "order_create" } }), "preview");
  assert.equal(
    phaseOf({ status: "pending", review: null, error: { unresolved: true } }),
    "unresolved",
  );
  assert.deepEqual(
    compareFindings(
      { raised: ["a", "b"], cleared: ["c"] },
      { raised: [{ class_id: "a" }], cleared: [] },
    ),
    {
      raised: [
        { id: "a", met: true },
        { id: "b", met: false },
      ],
      cleared: [{ id: "c", met: false }],
    },
  );
  assert.equal(rowIsNew({ id: "com_1", other: 3 }, new Set(["com_1"])), true);
  assert.equal(rowIsNew({ id: "com_2" }, new Set(["com_1"])), false);
});

test("Free Play keeps an opened company on reload and resets chat when switching companies", async () => {
  const { readSelection, selectionUrl, companySelection } =
    await import("../src/unified/routing.ts");
  const opened = readSelection(
    new URL("https://example.test/app/free-play?tenant=company&play=chat&session=conversation"),
  );
  const reopened = readSelection(new URL(selectionUrl(opened), "https://example.test"));
  assert.equal(reopened.freePlayChat, true);
  assert.equal(reopened.tenant, "company");
  assert.equal(reopened.session, "conversation");
  const switched = companySelection(opened, "other");
  assert.equal(switched.freePlayChat, false);
  assert.equal(switched.session, "");
  assert.equal(selectionUrl(switched), "/app/free-play?tenant=other");
});
