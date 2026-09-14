# Voice

How a Reality blog post reads. This file is the authority; `.claude/skills/blog-post` loads it
rather than restating it.

## Who is writing

One person, in the first person: a founder who ran a business and writes the code. That has three
consequences.

- **Lived detail beats abstraction.** Name the join written for the fourth time, the migration that
  touched nine tables, the quantity that went from twelve to eight at 14:03. A reader who has done
  this work recognises the detail and trusts the argument that follows.
- **No consultant register.** No "holistic", "seamless", "next generation", "game changer",
  "revolutionise". If a sentence would survive being pasted into any vendor's brochure, it is not
  this voice.
- **Business and code words used plainly.** Customer, warehouse, invoice, deadline. Job, column,
  schema, migration. Never explain them; the reader has them.

Be generous about the past. Seven hundred tables was not incompetence — every one was added by
someone solving a real problem under a real deadline. A post that sneers at conventional ERP loses
the only readers worth having.

## Length

Aim for about two and a half minutes of reading: roughly 450-550 words of prose. Bullets and table
rows read far faster per word, so a list-led post can total around 700 words and still read in that
time — judge the minutes, not the count. A reader who finishes is worth more than a reader impressed
by the length. If a passage cannot be cut without losing a core message, keep it; if it can, cut it.

## What every post does

- States its claim in the first three paragraphs, never saves it for the conclusion.
- Carries the argument with one concrete situation and real quantities.
- Links every claim about how Reality behaves to the guide, catalog or specification that
  establishes it. The blog argues; it never restates a contract.
- Ends with two or three links and one line naming the next post.
- Puts the pivot on its own line when there is one. "An agent supplies nothing." A single short
  sentence alone on a line is the strongest tool in the piece — use it once per post, not three
  times.

## English

Canonical. Plain declarative sentences, British spelling, no exclamation marks. Prefer the short
Anglo-Saxon word. Em dashes are allowed but rationed: at most one per paragraph.

## German

Not a translation. Written in German from the start, from the same notes, allowed to use different
examples as long as it makes the same claim. Translating the English sentence by sentence is the
single most common way these posts go wrong.

**Address the reader as `du`.** Lower case, throughout, including `dir`, `dich`, `dein`. Never
`Sie`, never mixed within a post.

**Write German sentences, not English ones in German words.** The tell is a nominalised subject
where German wants a clause:

- No: _Für einen Leser ohne Gedächtnis zu entwerfen ändert, was das System speichern muss._
- Yes: _Wenn du für einen Leser baust, der kein Gedächtnis hat, ändert sich, was das System
  speichern muss._

**Break long sentences.** German tolerates length, this voice does not. A four-part enumeration
becomes its own short sentence, or a question:

- No: _war das ein Storno, eine Teillieferung, ein korrigierter Tippfehler oder eine Rundung?_
- Yes: _Storno? Teillieferung? Tippfehler? Rundung?_

**Prefer the verb over the noun.** `Das zu beantworten hieß, drei Protokolle zu korrelieren` becomes
`Um das zu beantworten, musste ich drei Protokolle nebeneinanderlegen`.

**Use spoken forms.** `Schemas` not `Schemata`, `sowas` not `etwas dergleichen`, `rausfinden` not
`herausfinden` where the rhythm wants it, `Firma` alongside `Unternehmen`.

**Keep the canonical model terms in English**, unchanged and uninflected: SourceRecord, Document,
DocumentLine, Commitment, Reservation, Movement, LedgerEntry, SettlementAllocation, Fact, Business
Event. The documentation contract enforces this. Everything around them is German.

**Use German quotation marks** („so") and the German thousands and decimal conventions.

## Words we do not use

_Lösung_ for anything we built, _Journey_, _Mindset_, _Deep Dive_, _Learnings_, _spannend_ as the
only reason something matters, _revolutionär_, _disruptiv_, _KI-getrieben_. Say what the thing does
instead.

## Before publishing

- Read the German aloud. Any sentence that needs a second run to parse gets broken up.
- Check that `du` is consistent and that no `Sie` survived.
- Check the word count against the target above.
- Confirm every product claim has a link behind it.
