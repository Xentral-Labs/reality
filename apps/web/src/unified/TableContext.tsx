import { createContext, useContext, type ReactNode } from "react";
import type { TableQuery } from "../api";
import type { Selection } from "./routing";
export function tableIdentity(s: Selection) {
  const variant =
    s.route === "orders-deliveries"
      ? s.ordersView
      : s.route === "warehouse"
        ? s.warehouseView
        : s.route === "finance"
          ? s.financeView
          : s.route === "master-data"
            ? s.family
            : s.route === "data-sources"
              ? s.dataView
              : "";
  return `${s.route}${variant ? ":" + variant : ""}`;
}
const Context = createContext<{
  user: string;
  scope: string;
  id: string;
  query: TableQuery;
  change: (values: Partial<Selection>) => void;
} | null>(null);
export function TableProvider({
  user,
  selection,
  navigate,
  children,
}: {
  user: string;
  selection: Selection;
  navigate: (changes: Partial<Selection>) => void;
  children: ReactNode;
}) {
  const id = tableIdentity(selection);
  const query: TableQuery = {
    size: selection.tableSize,
    sort: selection.tableScope === id ? selection.tableSort : "",
    sort_direction: selection.tableDirection,
  };
  return (
    <Context.Provider
      value={{
        user,
        scope: JSON.stringify(selection),
        id,
        query,
        change: (values) => navigate({ ...values, tableScope: id, page: 1, entry: "", record: "" }),
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useTableContext() {
  return useContext(Context);
}
export function useRegisterQuery() {
  return useContext(Context)?.query || {};
}
