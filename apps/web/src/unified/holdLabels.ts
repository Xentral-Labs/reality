import { t } from "../localization";

export function holdReason(code: string): string {
  const labels: Record<string, string> = {
    credit_check: "Credit check",
    customer_request: "Customer request",
    address_clarification: "Address clarification",
    compliance: "Compliance review",
    manual_review: "Manual review",
    other: "Other hold reason",
  };
  return t(labels[code] || "Other hold reason");
}
