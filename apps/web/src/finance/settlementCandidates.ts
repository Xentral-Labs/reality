// Feature 168: read-time candidates for an unallocated customer payment.
// The backend states the reasons; this module only orders and labels them.

export type InvoiceChoice = {
  id: string;
  number: string;
  open: string;
  currency: string;
  reasons?: string[];
};

/** Choices that carry at least one reason, in the order the backend ranked them. */
export function suggestedInvoices(choices: InvoiceChoice[] | undefined): InvoiceChoice[] {
  return (choices || []).filter((choice) => (choice.reasons || []).length > 0);
}

/** English source label for a backend reason; unknown reasons pass through unchanged. */
export function reasonLabel(reason: string): string {
  const labels: Record<string, string> = {
    "amount equals the open amount": "Amount equals the open amount",
    "invoice number appears in the remittance text":
      "Invoice number appears in the remittance text",
    "stated reference names this invoice among others":
      "Stated reference names this invoice among others",
  };
  return labels[reason] || reason;
}
