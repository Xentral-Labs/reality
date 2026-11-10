# Combined order proposal contract

Two methods only: shopify_source_order_prepare(propose) and
shopify_source_order_review(read). No apply method or generic executor.

Prepare binds exact source/job/hash/positive version plus request UUID and verified
buyer review/digest. Explicit company/location IDs and complete source-line/item/
stock-unit/same-unit selections are required. Optional expected master digests
constrain proposal creation; when absent, fresh labels/digests are frozen for the
subsequent exact human/policy review, never claimed already approved.

Raw original-line evidence is retained unchanged in the full plan but not duplicated
into chat wire. Review projection exposes ALL prospective business-effect arguments
and explicit links to original evidence. Wire max24000 UTF-8 bytes, at most100 lines;
no silent omission of effect parameters. A too-large review refuses safely.

Dedicated Action type is non-executable. Missing structure does not create a fake
full proposal. Unknown final price/line amount/date/calendar/credit remains held;
observed original price is evidence only. Server accepts no caller amount overrides.
Later exact human/standing-mandate acceptance must authorize the SAME bundle/plan,
use truthful external attribution and canonical application; it is not implemented
or implied by this proposal-only purpose.
