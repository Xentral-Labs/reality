import { useEffect, useRef, useState } from "react";
import { searchApi, type SearchPage, type SearchProvider } from "../api";
export const searchProviders: SearchProvider[] = [
  "partners",
  "items_locations",
  "orders",
  "finance",
  "shipping",
  "reality",
  "reports",
];
export const searchFamilies: Record<SearchProvider, string[]> = {
  partners: ["party"],
  items_locations: ["item", "location"],
  orders: ["customer_order", "supplier_order"],
  finance: [
    "customer_invoice",
    "supplier_invoice",
    "customer_credit",
    "supplier_credit",
    "payment",
  ],
  shipping: ["shipment"],
  reality: [
    "document",
    "source_record",
    "commitment",
    "reservation",
    "movement",
    "fact",
    "ledger_entry",
  ],
  reports: ["private_report"],
};
export type ProviderState = { data?: SearchPage; loading: boolean; error?: string };

/** Scope and generation guards supplement cancellation; at most three requests are in flight. */
export function useCommandSearch(
  tenant: string,
  query: string,
  language: string,
  filter: string,
  expanded: string,
  page: number,
  family: string,
) {
  const [attempt, setAttempt] = useState<{ provider?: SearchProvider; revision: number }>({
    revision: 0,
  });
  const [state, setState] = useState<{
    scope: string;
    providers: Partial<Record<SearchProvider, ProviderState>>;
  }>({ scope: "", providers: {} });
  const latest = useRef(state);
  latest.current = state;
  const generation = useRef(0);
  const scope = JSON.stringify([tenant, query, language, filter, expanded, family, page]);
  useEffect(() => {
    const current = ++generation.current;
    const controller = new AbortController();
    const providers = searchProviders.filter(
      (provider) =>
        (!family || searchFamilies[provider].includes(family)) &&
        (expanded
          ? expanded === provider
          : filter === "all" ||
            (filter === "records" ? provider !== "reports" : filter === provider)),
    );
    const sameScope = latest.current.scope === scope;
    const requested =
      sameScope && attempt.provider
        ? providers.filter(
            (provider) =>
              provider === attempt.provider || latest.current.providers[provider]?.loading,
          )
        : providers;
    if (!query.trim() || query.length > 500 || !providers.length) {
      setState({ scope, providers: {} });
      return () => controller.abort();
    }
    setState({
      scope,
      providers: {
        ...(sameScope ? latest.current.providers : {}),
        ...Object.fromEntries(requested.map((key) => [key, { loading: true }])),
      },
    });
    const publish = (provider: SearchProvider, value: ProviderState) => {
      if (controller.signal.aborted || current !== generation.current) return;
      setState((previous) =>
        previous.scope === scope
          ? { ...previous, providers: { ...previous.providers, [provider]: value } }
          : previous,
      );
    };
    const timer = window.setTimeout(async () => {
      let index = 0;
      const work = async () => {
        while (index < requested.length && !controller.signal.aborted) {
          const provider = requested[index++];
          let result: SearchPage | undefined;
          const items: SearchPage["items"] = [];
          try {
            // Keep all consumed source lookahead while assembling later merged pages.
            do {
              result = await searchApi.query(
                tenant,
                {
                  query,
                  provider,
                  language,
                  limit: expanded ? 50 : 4,
                  ...(family && filter === "records" ? { family } : {}),
                  cursor: result?.next_cursor,
                },
                controller.signal,
              );
              items.push(...result.items);
            } while (expanded && result.has_more && items.length < (page + 1) * 50);
            publish(provider, { data: { ...result, items }, loading: false });
          } catch (error) {
            if (!controller.signal.aborted)
              publish(provider, {
                ...(result ? { data: { ...result, items } } : {}),
                loading: false,
                error:
                  error instanceof Error
                    ? error.message
                    : "Search is temporarily unavailable. Please retry.",
              });
          }
        }
      };
      await Promise.all(Array.from({ length: Math.min(3, requested.length) }, work));
    }, 150);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [scope, attempt]);
  return {
    providers: state.scope === scope ? state.providers : {},
    retry: (provider?: SearchProvider) =>
      setAttempt((value) => ({ provider, revision: value.revision + 1 })),
  };
}
