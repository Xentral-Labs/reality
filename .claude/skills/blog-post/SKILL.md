---
name: blog-post
description: Write, revise or publish a post on the Reality blog (apps/docs/content/blog and its German edition). Use when asked to draft a blog post or article, rewrite one, translate or fix the German edition, pick the next topic from the editorial backlog, or publish a draft. Loads the editorial voice guide first so both language editions read as the founder rather than as documentation.
---

# Writing a Reality blog post

## Read these first, every time

1. `apps/docs/editorial/voice.md` — how a post reads. The authority on voice, length and the German
   `du` rules. Do not write a sentence before reading it.
2. `apps/docs/editorial/README.md` — the pipeline, the definition of done, the distribution
   checklist.
3. `apps/docs/editorial/ideas.md` — the backlog and what stage each idea is at.

Never restate the rules from `voice.md` here or in a commit message. That file changes; a copy of it
would drift.

## Scaffold, do not hand-create

```bash
cd apps/docs && npm run blog:new -- <slug>
```

This writes both language editions from separate templates, sets today's date and `draft: true`, and
refuses to overwrite. Creating only one edition breaks the documentation contract, which requires
every page to exist in both languages **and** to differ in content.

A slug is lowercase words joined by hyphens, carries no date, and must not change after publishing —
it is the address.

## Write the English edition, then write the German one

Write English first; it is canonical. Then write German **from the same notes, not from the English
sentences**. Re-reading the English paragraph by paragraph and rendering it in German is how these
posts go wrong: the result is grammatical and reads like a translation. Work from the claim, in
German, and let the sentences come out German-shaped. Different examples are allowed as long as the
claim is the same.

## Keep drafts as drafts

`draft: true` keeps a post out of the index and both feeds while still building at its own address,
so it can be committed, previewed and reviewed. Remove the mark only when the post ships, and remove
it in both editions at once — a contract asserts that an article is a draft in every language or in
none.

## Finish

```bash
cd apps/docs && npm run format && npm run test && npm run build
```

The build fails on a dead link, which is the check that catches a link to a page that does not exist
on `main` yet.

Then move the idea's row in `apps/docs/editorial/ideas.md` to the stage it reached, and work the
distribution checklist in `editorial/README.md`. The canonical URL is always
`docs.runreality.ai/blog/<slug>`; everything published elsewhere links back to it.

## To read it as a reader will

```bash
cd apps/docs && npm run build && npm run preview -- --port 4173
```

For the real static container instead, `make docs` serves it on port 8083 with the configured public
origin and the nginx feed content type. It rebuilds the image, so it captures the source as of when
the build starts — re-run it after further edits.
