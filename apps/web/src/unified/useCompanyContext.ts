import { tableIdentity } from "./TableContext";
import { useEffect, useState } from "react";
import { api, type Bootstrap } from "../api";
import { companySelection, readSelection, selectionUrl, type Selection } from "./routing";

export function useCompanyContext() {
  const [selection, setSelection] = useState(() => readSelection(new URL(location.href)));
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api
      .bootstrap()
      .then((value) => {
        if (!active) return;
        setBootstrap(value);
        if (!selection.tenant && value.default_tenant_id) {
          const next = companySelection(selection, value.default_tenant_id);
          history.replaceState(null, "", selectionUrl(next));
          setSelection(next);
        }
      })
      .catch((reason) => {
        if (active) setError(String(reason.message));
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    const update = () => setSelection(readSelection(new URL(location.href)));
    addEventListener("popstate", update);
    return () => removeEventListener("popstate", update);
  }, []);
  const navigate = (changes: Partial<Selection>, options?: { replace?: boolean }) => {
    const next = { ...selection, ...changes };
    if (tableIdentity(next) !== tableIdentity(selection)) {
      next.tableSort = "";
      next.tableScope = "";
      next.tableDirection = "asc";
      next.page = 1;
    }
    if (options?.replace) history.replaceState(null, "", selectionUrl(next));
    else history.pushState(null, "", selectionUrl(next));
    setSelection(next);
  };
  return {
    bootstrap,
    openCompany: (data: Bootstrap, id: string) => {
      if (!data.tenants.some((row) => row.id === id)) return;
      setBootstrap(data);
      navigate({ ...companySelection(selection, id), route: "settings", settingsView: "company" });
    },
    error,
    selection,
    navigate,
    company: bootstrap?.tenants.find((row) => row.id === selection.tenant),
    switchCompany: (tenant: string) => navigate(companySelection(selection, tenant)),
  };
}

/**
 * A changing company key unmounts consumers; generations also discard obsolete reads.
 * A reload keeps the previous answer so pages dim it instead of collapsing to a
 * placeholder, and only the first read of a query shows one. A failed reload drops the
 * previous answer, so a stale table can never stand in for a read that did not happen.
 */
export function useRead<T>(load: () => Promise<T>, keys: unknown[]) {
  const [state, setState] = useState<{
    data?: T;
    error?: string;
    /** Machine-readable classification the API attached to the error, when it did. */
    code?: string;
    loading: boolean;
  }>({
    loading: true,
  });
  const [revision, refresh] = useState(0);
  useEffect(() => {
    const changed = () => refresh((value) => value + 1);
    window.addEventListener("reality:delivery-settled", changed);
    return () => window.removeEventListener("reality:delivery-settled", changed);
  }, []);
  useEffect(() => {
    let current = true;
    setState((previous) => ({ data: previous.data, loading: true }));
    load()
      .then((data) => {
        if (current) setState({ data, loading: false });
      })
      .catch((error) => {
        if (current)
          setState({
            error: String(error.message),
            code: typeof error.code === "string" ? error.code : undefined,
            loading: false,
          });
      });
    return () => {
      current = false;
    };
  }, [...keys, revision]);
  return { ...state, refresh: () => refresh((value) => value + 1) };
}
