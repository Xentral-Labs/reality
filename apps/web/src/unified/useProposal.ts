import { useEffect, useRef } from "react";
import { deliveryActions, type DeliveryProposal } from "../api";

/** Reconcile connectivity with read-only status calls; never retry a mutation. */
export function useProposalRecovery<T extends { status: string } = DeliveryProposal>(
  tenant: string,
  id: string,
  enabled: boolean,
  receive: (value: T) => void,
  failed: (message: string) => void,
  read?: (tenant: string, id: string) => Promise<T>,
) {
  const callbacks = useRef({ receive, failed });
  callbacks.current = { receive, failed };
  useEffect(() => {
    if (!id || !enabled) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const result = await (read ? read(tenant, id) : deliveryActions.detail(tenant, id));
        if (!active) return;
        callbacks.current.receive(result as T);
        if (result.status === "executing") timer = setTimeout(poll, 2000);
      } catch (reason) {
        if (active) callbacks.current.failed((reason as Error).message);
      }
    };
    void poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [tenant, id, enabled]);
}
