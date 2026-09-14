import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const content = fileURLToPath(new URL("../content/", import.meta.url));

for (const locale of ["", "de/"]) {
  const frontmatter = fs
    .readFileSync(path.join(content, locale, "index.md"), "utf8")
    .split("---")[1];
  const actions = frontmatter.split("  actions:\n")[1].split("\nfeatures:")[0];
  test(`${locale || "en/"} home links resolve to real pages with canonical directory handling`, () => {
    for (const [, link] of frontmatter.matchAll(/^\s+link: (\/\S+)$/gmu)) {
      const target = path.join(content, link.slice(1));
      const candidates = link.endsWith("/")
        ? [path.join(target, "index.md")]
        : [target + ".md", path.join(target, "index.md")];
      assert.ok(
        candidates.some((candidate) => fs.existsSync(candidate)),
        `Broken home link: ${link}`,
      );
      if (locale) assert.ok(link.startsWith("/de/"), `Wrong language: ${link}`);
    }
  });
  test(`${locale || "en/"} home prioritizes learning and has one final product action`, () => {
    const links = [...actions.matchAll(/^\s+link: (\S+)$/gmu)].map((match) => match[1]);
    assert.equal(links[0], `/${locale}concepts/business-reality-guide`);
    assert.match(actions, /^\s+- theme: brand/u);
    assert.equal(links.filter((link) => link === "__APP_URL__").length, 1);
    assert.equal(links.at(-1), "__APP_URL__");
  });
}
