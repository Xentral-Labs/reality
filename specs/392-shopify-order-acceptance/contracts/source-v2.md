# Source acquisition v2 selection

Preserve the unmodified selected data.order object. The old query/digest remains
unchanged. A new fixed query adds all fields below to the existing388/391 shape.

Order scalars: processedAt, edited (cancelledAt already selected).
MoneyBags each selecting shopMoney { amount currencyCode }:
subtotalPriceSet,currentSubtotalPriceSet,currentTotalPriceSet,
totalDiscountsSet,currentTotalDiscountsSet,totalTaxSet,currentTotalTaxSet,
totalShippingPriceSet,currentShippingPriceSet,totalRefundedSet,totalTipReceivedSet,
originalTotalDutiesSet,currentTotalDutiesSet,originalTotalAdditionalFeesSet,
currentTotalAdditionalFeesSet.

Complete nonpaginated order additionalFees { id }; on EVERY selected line:
originalTotalSet { shopMoney { amount currencyCode } } and duties { id }.
Complete <=100 line membership, unchanged currentQuantity==quantity, editedfalse,
no cancellation and explicitly zero refunds required. No PII or new scope.

Fee nullable pair plus explicitly empty additionalFees yields not_applicable;
duty nullable pair plus ALL complete unchanged source line duties[] +editedfalse
+explicitzeroRefunds yields not_applicable_no_line_duties. Neither manufactures
numeric0. Missing, nonempty, partial or changed evidence is held. Other ancillary
money must be explicitly stated0/samecurrency. Source unit/line/order amounts
are COPIED; arithmetic only compares eligibility. No approximate discounted price.

Official2026-07 primary evidence:
https://shopify.dev/docs/api/admin-graphql/2026-07/objects/Order
https://shopify.dev/docs/api/admin-graphql/2026-07/objects/LineItem
https://shopify.dev/docs/api/admin-graphql/2026-07/objects/AdditionalFee
https://shopify.dev/docs/api/admin-graphql/2026-07/objects/Duty

Existing389 buyer receipts remain mapping-only historical evidence; they are not
authoritative overall intake state. Successor wire omits legacy remaining_review
and current_basis labels, explicitly marks buyer/evidence historical scope, and
uses dedicated successor status as authoritative acceptance reconciliation.391
stored contracts/digests and389 wire remain unchanged.

A pre-existing narrower v1 capture at the SAME upstream updatedAt cannot silently
be replaced by a richer selection. Canonical source conflict rules remain intact.
This packet supports a genuinely new/current v2 source (including new orders first
captured with v2); enriching an unchanged previously captured version requires a
separately reviewed source-profile transition. Never fabricate updatedAt, mutate
the original or perform a Shopify edit just to make a capture appear current.
