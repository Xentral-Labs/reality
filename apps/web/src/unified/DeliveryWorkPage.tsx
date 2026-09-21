import { useEffect } from "react";
import type { Selection } from "./routing";

// Compatibility for saved links to the unified work list. Returned-goods
// disposition is available from the warehouse movement actions there.
export function DeliveryWorkPage({
  selection,
  navigate,
}: {
  selection: Selection;
  navigate: (changes: Partial<Selection>, options?: { replace?: boolean }) => void;
}) {
  useEffect(() => {
    navigate(
      {
        route: "orders-deliveries",
        ordersView: "deliveries",
        entry: "",
        commitment: selection.commitment,
      },
      { replace: true },
    );
  }, [selection.commitment, navigate]);
  return null;
}
