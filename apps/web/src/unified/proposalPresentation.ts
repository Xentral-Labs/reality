const proposalBusinessLabels: Record<string, string> = {
  intake_apply: "Review source meaning",
  intake_batch_apply: "Review selected sources",
  intake_mandate_grant: "Grant review mandate",
  intake_mandate_revoke: "Revoke review mandate",
  reserve: "Reserve stock",
  reservation_release: "Release reservation",
  commitment_hold: "Hold commitment",
  commitment_hold_release: "Release commitment hold",
  party_delivery_hold: "Place customer delivery hold",
  party_delivery_hold_release: "Release customer delivery hold",
  movement_create: "Record movement",
  movement_correct: "Correct movement",
  ledger_reverse: "Reverse posting",
  order_create: "Create order",
  sales_invoice_record: "Record sales invoice",
  supplier_invoice_record: "Record supplier invoice",
  sales_credit_record: "Record sales credit",
  customer_refund_post: "Record refund",
  customer_payment_post: "Record customer payment",
  supplier_payment_post: "Record supplier payment",
  party_create: "Create party",
  party_update: "Update party",
  item_create: "Create item",
  item_update: "Update item",
  location_create: "Create location",
  location_update: "Update location",
  payment_term_create: "Create payment term",
  payment_term_update: "Update payment term",
  reorder_point_set: "Set reorder point",
  reorder_point_remove: "Remove reorder point",
};

export const proposalBusinessLabelEntries = Object.entries(proposalBusinessLabels);

export function proposalBusinessLabel(tool: string, fallback: string): string {
  return proposalBusinessLabels[tool] || fallback;
}
