# Editorial

This directory is the editorial desk for the [Reality Blog](../content/blog/index.md). It is **not
published**: VitePress builds only `content/`, so nothing here reaches the web.

- [`voice.md`](./voice.md) — how a post reads: who is writing, the length target, and the German
  `du` rules. The authority on voice; read it before writing a sentence.
- [`ideas.md`](./ideas.md) — the board. Every idea lives here from first thought to published.
- [`templates/`](./templates) — the English and German post skeletons used by the scaffolding
  script.

## The pipeline

An idea moves through four states, and each one is a section in `ideas.md`.

**Backlog** — anything worth writing one day. One line is enough. Do not self-censor here; the cost
of a bad line in the backlog is zero.

**Next** — accepted, has an angle and a target date. Promote an idea only when you can state its
claim in one sentence without using the word "and".

**Drafting** — a slug exists on disk in both languages. Scaffold it with:

```bash
npm run blog:new -- order-changed-after-shipping
```

Claude Code has a `blog-post` skill in `.claude/skills/` that loads `voice.md` and walks this
pipeline. The command writes `content/blog/<slug>.md` and `content/de/blog/<slug>.md` from the
templates, refuses to overwrite an existing file, and sets today's date. Keep `draft: true` in the
frontmatter until the post is finished: drafts are excluded from the index page and from both RSS
feeds, so an unfinished post can be committed and previewed without being announced.

**Published** — `draft` is removed, both languages are live, and the distribution checklist below is
done. Move the row into the Published section with its real date.

## Definition of done

A post ships when all of these are true.

- The claim is stated in the first three paragraphs, not in the conclusion.
- At least one concrete business situation with real quantities carries the argument.
- Every assertion about how Reality behaves links to the guide, catalog or spec that proves it.
- The German edition is written, not translated word for word, addresses the reader as `du`, and
  reads as German rather than as English in German words. It is allowed to use different examples as
  long as it makes the same claim. [`voice.md`](./voice.md) has the rules and the before/after
  examples.
- The body reads in about two and a half minutes. A reader who finishes is worth more than one
  impressed by the length.
- `npm run test` and `npm run format:check` pass. The contract test enforces that both language
  editions exist and differ.

## Distribution checklist

The canonical URL is always `docs.runreality.ai/blog/<slug>`. Everywhere else links back to it.

- [ ] LinkedIn: full text as a post, canonical link in the last line, not in a comment.
- [ ] Newsletter: full text, canonical link at the top.
- [ ] dev.to or Lobsters: only for the technically-grounded posts, with `canonical_url` set.
- [ ] Internal: drop the link in the team channel so support and sales can reuse the framing.

## Knowing whether anyone read it

Reader analytics is optional and self-hosted; see **Reader analytics** in the repository README for
how to start it and how to switch it on for a build. It is off in local development and in CI by
design.

Three numbers are worth looking at after a post. Everything else is noise.

- **Average time on the page.** Measured out of the box. A post with high traffic and a short
  average visit had a good headline and a weak argument. Real completion needs a custom scroll
  event, which is not wired up yet.
- **Return readers.** Measured out of the box, and the only number that says whether the blog is
  becoming a habit rather than a series of lucky links.
- **Onward clicks into the guide.** Which post sends the most readers into
  `/concepts/business-reality-guide`. That tells you which angle creates real interest in the model,
  which page views cannot.

Do not optimise for page views. A post that goes wide on LinkedIn and sends nobody into the guide
taught you something about LinkedIn, not about the argument.

## What we do not write

Keeping this list short is what keeps the blog worth subscribing to.

- Product announcements. Those belong in the changelog.
- Generic "AI will change everything" commentary with no ERP situation in it.
- Competitor comparisons.
- Anything whose claim cannot be checked against the repository.
