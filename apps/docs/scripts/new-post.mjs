#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const editions = [
  { locale: "en", template: "post.en.md", directory: path.join("content", "blog") },
  { locale: "de", template: "post.de.md", directory: path.join("content", "de", "blog") },
];

const fail = (message) => {
  process.stderr.write(`${message}\n`);
  process.exit(1);
};

const [slug, ...rest] = process.argv.slice(2);

if (!slug || slug.startsWith("-")) {
  fail(
    [
      'Usage: npm run blog:new -- <slug> [--date YYYY-MM-DD] [--author "Name"]',
      "",
      "Creates the English and German editions of one post from editorial/templates/.",
      "Both start with draft: true, so they stay out of the index and both RSS feeds.",
    ].join("\n"),
  );
}

if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(slug)) {
  fail(`Slug must be lowercase words joined by single hyphens: ${slug}`);
}

const option = (name, fallback) => {
  const index = rest.indexOf(`--${name}`);
  return index === -1 ? fallback : rest[index + 1] || fallback;
};

const date = option("date", new Date().toISOString().slice(0, 10));
if (!/^\d{4}-\d{2}-\d{2}$/u.test(date)) fail(`Date must be YYYY-MM-DD: ${date}`);

const author = option("author", "Benedikt Sauter");
const title = slug.replaceAll("-", " ").replace(/^./u, (character) => character.toUpperCase());

const targets = editions.map((edition) => ({
  ...edition,
  file: path.join(docsRoot, edition.directory, `${slug}.md`),
}));

const existing = targets.filter((target) => fs.existsSync(target.file));
if (existing.length > 0) {
  fail(
    `Refusing to overwrite:\n${existing
      .map((target) => `  ${path.relative(docsRoot, target.file)}`)
      .join("\n")}`,
  );
}

for (const target of targets) {
  const template = fs.readFileSync(
    path.join(docsRoot, "editorial", "templates", target.template),
    "utf8",
  );
  const body = template
    .replaceAll("%%TITLE%%", title)
    .replaceAll("%%DATE%%", date)
    .replaceAll("%%AUTHOR%%", author)
    .replaceAll(
      "%%DESCRIPTION%%",
      target.locale === "de"
        ? "Eine Zeile, die die These wiedergibt. Erscheint in der Übersicht und im RSS-Feed."
        : "One line carrying the claim. It appears on the index page and in the RSS feed.",
    )
    .replaceAll("%%NEXT%%", target.locale === "de" ? "noch offen." : "still to be decided.");
  fs.mkdirSync(path.dirname(target.file), { recursive: true });
  fs.writeFileSync(target.file, body, "utf8");
}

process.stdout.write(
  [
    "Created:",
    ...targets.map((target) => `  ${path.relative(docsRoot, target.file)}`),
    "",
    "Next:",
    "  1. Replace the title, description and body in both editions.",
    "  2. Move the idea into the Drafting section of editorial/ideas.md.",
    "  3. Remove `draft: true` when the post is ready to be announced.",
    "  4. Run `npm run format` and `npm run test`.",
    "",
  ].join("\n"),
);
