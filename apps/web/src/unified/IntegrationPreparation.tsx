import { useEffect, useRef, useState } from "react";
import { Cable, Search } from "lucide-react";
import { t } from "../localization";

const categories = ["Shop & ERP", "Payments", "CRM", "Product data / PIM"];
const areas = {
  orders: "Orders",
  customers: "Customers",
  products: "Product data",
  payments: "Payments",
  refunds: "Refunds",
  payouts: "Payouts",
  contacts: "Contacts",
  companies: "Companies",
  deals: "Deals",
  media: "Product media",
  categories: "Product categories",
};
type Area = keyof typeof areas;
type Provider = {
  id: string;
  name: string;
  badge: string;
  category: string;
  purpose: string;
  areas: Area[];
};
const providers: Provider[] = [
  {
    id: "shopify",
    name: "Shopify",
    badge: "S",
    category: categories[0],
    purpose: "Plan to receive orders, customers and products from your shop.",
    areas: ["orders", "customers", "products"],
  },
  {
    id: "shopware6",
    name: "Shopware 6",
    badge: "sw",
    category: categories[0],
    purpose: "Plan to receive orders, customers and products from your shop.",
    areas: ["orders", "customers", "products"],
  },
  {
    id: "xentral",
    name: "Xentral",
    badge: "x",
    category: categories[0],
    purpose: "Plan to receive orders and master data from your ERP.",
    areas: ["orders", "customers", "products"],
  },
  {
    id: "shopify-payments",
    name: "Shopify Payments",
    badge: "S",
    category: categories[1],
    purpose: "Plan payment data for a related Shopify shop.",
    areas: ["payments", "refunds", "payouts"],
  },
  {
    id: "stripe",
    name: "Stripe",
    badge: "s",
    category: categories[1],
    purpose: "Plan to receive payments, refunds and payouts.",
    areas: ["payments", "refunds", "payouts"],
  },
  {
    id: "paypal",
    name: "PayPal",
    badge: "P",
    category: categories[1],
    purpose: "Plan to receive payments and refunds.",
    areas: ["payments", "refunds"],
  },
  {
    id: "hubspot",
    name: "HubSpot",
    badge: "H",
    category: categories[2],
    purpose: "Plan to receive contacts, companies and sales opportunities.",
    areas: ["contacts", "companies", "deals"],
  },
  {
    id: "salesforce",
    name: "Salesforce",
    badge: "sf",
    category: categories[2],
    purpose: "Plan to receive contacts, companies and sales opportunities.",
    areas: ["contacts", "companies", "deals"],
  },
  {
    id: "akeneo",
    name: "Akeneo",
    badge: "a",
    category: categories[3],
    purpose: "Plan to receive enriched product information and categories.",
    areas: ["products", "categories", "media"],
  },
  {
    id: "pimcore",
    name: "Pimcore",
    badge: "p",
    category: categories[3],
    purpose: "Plan to receive enriched product information and categories.",
    areas: ["products", "categories", "media"],
  },
];
type Draft = { id: string; provider: string; name: string; shop: string; areas: Area[] };
function validDraft(value: unknown): value is Draft {
  if (!value || typeof value !== "object") return false;
  const d = value as Draft,
    p = providers.find((p) => p.id === d.provider);
  return (
    !!p &&
    typeof d.id === "string" &&
    d.id.length > 0 &&
    d.id.length <= 100 &&
    typeof d.name === "string" &&
    !!d.name.trim() &&
    d.name.length <= 100 &&
    typeof d.shop === "string" &&
    d.shop.length <= 100 &&
    (p.id !== "shopify-payments" || !!d.shop.trim()) &&
    Array.isArray(d.areas) &&
    d.areas.length > 0 &&
    d.areas.length <= p.areas.length &&
    new Set(d.areas).size === d.areas.length &&
    d.areas.every((a) => p.areas.includes(a))
  );
}
function loadDrafts(key: string): { drafts: Draft[]; error: boolean } {
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem(key) || "[]");
    if (
      !Array.isArray(saved) ||
      saved.length > 100 ||
      !saved.every(validDraft) ||
      new Set(saved.map((d) => d.id)).size !== saved.length
    )
      throw new Error("Invalid drafts");
    return { drafts: saved, error: false };
  } catch {
    return { drafts: [], error: true };
  }
}
export function IntegrationPreparation({
  tenant,
  user,
  prepareRequest,
  importItems,
}: {
  tenant: string;
  user: string;
  prepareRequest: number;
  importItems: () => void;
}) {
  const key = `reality.integration-preparations.v1:${encodeURIComponent(user)}:${encodeURIComponent(tenant)}`;
  const [state, setState] = useState(() => loadDrafts(key));
  const [editor, setEditor] = useState<{ draft?: Draft } | null>(null);
  const [notice, setNotice] = useState("");
  // The page's Add integration action counts requests; each new one opens a fresh draft
  // editor. A remount (company switch) does not replay the last request.
  const handledRequest = useRef(prepareRequest);
  useEffect(() => {
    if (prepareRequest === handledRequest.current) return;
    handledRequest.current = prepareRequest;
    setNotice("");
    setEditor({});
  }, [prepareRequest]);
  function persist(drafts: Draft[]) {
    try {
      sessionStorage.setItem(key, JSON.stringify(drafts));
      setState({ drafts, error: false });
      return true;
    } catch {
      setNotice("Draft could not be saved. Browser session storage is unavailable.");
      return false;
    }
  }
  return (
    <section
      className="rounded-xl border border-border-default bg-surface p-5 sm:p-6"
      aria-label={t("Integration preparation")}
    >
      <p className="mt-4 rounded-lg bg-surface-muted p-3 text-sm text-fg-muted">
        {t(
          "Preparation only. Drafts stay in this browser session for you and this company. No system is connected and no data is synchronized.",
        )}
      </p>
      {state.error && (
        <p role="alert" className="mt-3 text-sm text-danger">
          {t("Saved preparations could not be loaded. You can start a new draft.")}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-3 text-sm">
          {t(notice)}
        </p>
      )}
      {!state.drafts.length ? (
        <div className="py-8 text-center">
          <Cable className="mx-auto mb-3 text-accent" size={28} />
          <h3 className="font-semibold">{t("Start with your first system")}</h3>
          <p className="mt-2 text-sm text-fg-muted">
            {t(
              "Shop, ERP, payments, CRM or product information: choose a provider to prepare its setup.",
            )}
          </p>
        </div>
      ) : (
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {state.drafts.map((d) => {
            const p = providers.find((p) => p.id === d.provider)!;
            return (
              <article key={d.id} className="min-w-0 rounded-xl border border-border-default p-4">
                <div className="flex items-center gap-3">
                  <Badge provider={p} />
                  <div className="min-w-0">
                    <p className="text-sm text-fg-muted" data-localization="original">
                      {p.name}
                    </p>
                    <h3 className="break-words font-semibold" data-localization="original">
                      {d.name}
                    </h3>
                  </div>
                </div>
                <span className="mt-4 inline-block rounded-md bg-surface-muted px-2 py-1 text-xs">
                  {t("Preparation draft")}
                </span>
                <p className="mt-3 text-sm text-fg-muted">
                  {d.areas.map((a) => t(areas[a])).join(" · ")}
                </p>
                {d.shop && (
                  <p className="mt-2 break-words text-sm">
                    {t("Related Shopify shop")}: <span data-localization="original">{d.shop}</span>
                  </p>
                )}
                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    className="br-btn"
                    onClick={() => {
                      setNotice("");
                      setEditor({ draft: d });
                    }}
                  >
                    {t("Open preparation")}
                  </button>
                  <button
                    className="br-btn"
                    onClick={() => {
                      if (persist(state.drafts.filter((row) => row.id !== d.id)))
                        setNotice("Draft removed.");
                    }}
                  >
                    {t("Remove draft")}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
      {editor && (
        <PreparationDialog
          draft={editor.draft}
          close={() => setEditor(null)}
          importItems={() => {
            setEditor(null);
            importItems();
          }}
          save={(draft) => {
            if (!editor.draft && state.drafts.length >= 100)
              return "This session has 100 drafts. Remove a draft before adding another.";
            if (!persist([...state.drafts.filter((d) => d.id !== draft.id), draft]))
              return "Draft could not be saved. Browser session storage is unavailable.";
            setEditor(null);
            setNotice("Preparation saved. The connection will be implemented separately.");
            return "";
          }}
        />
      )}
    </section>
  );
}
function Badge({ provider }: { provider: Provider }) {
  return (
    <span
      aria-hidden="true"
      data-localization="original"
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-lg font-bold text-accent"
    >
      {provider.badge}
    </span>
  );
}
function PreparationDialog({
  draft,
  close,
  save,
  importItems,
}: {
  draft?: Draft;
  close: () => void;
  save: (d: Draft) => string;
  importItems: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const [provider, setProvider] = useState<Provider | undefined>(() =>
    providers.find((p) => p.id === draft?.provider),
  );
  const [step, setStep] = useState(0);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [name, setName] = useState(draft?.name || "");
  const [shop, setShop] = useState(draft?.shop || "");
  const [selected, setSelected] = useState<Area[]>(draft?.areas || []);
  const [error, setError] = useState("");
  useEffect(() => {
    const trigger = document.activeElement as HTMLElement | null;
    const element = dialog.current!;
    element.showModal();
    return () => {
      element.close();
      trigger?.focus();
    };
  }, []);
  useEffect(() => {
    heading.current?.focus();
  }, [step, provider]);
  const filtered = providers.filter(
    (p) =>
      (!category || p.category === category) &&
      `${p.name} ${t(p.category)} ${t(p.purpose)}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
  );
  const steps = ["Name your connection", "Choose intended data", "Review preparation"];
  return (
    <dialog
      ref={dialog}
      aria-labelledby="preparation-title"
      onCancel={close}
      className="m-auto max-h-[90dvh] w-[min(880px,94vw)] min-w-0 overflow-auto rounded-xl border border-border-default bg-surface p-5 text-fg shadow-xl backdrop:bg-black/30 sm:p-7"
    >
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2
            id="preparation-title"
            ref={heading}
            tabIndex={-1}
            className="text-xl font-semibold text-fg-strong"
          >
            {provider ? t(steps[step]) : t("Add integration")}
          </h2>
          {provider && (
            <p className="mt-2 text-sm text-fg-muted" data-localization="original">
              {provider.name}
            </p>
          )}
        </div>
        <button className="br-btn" onClick={close}>
          {t("Close")}
        </button>
      </header>
      {!provider ? (
        <>
          <p className="mt-3 text-sm text-fg-muted">
            {t("Choose a provider. All connections below are preparation only.")}
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <label className="flex min-w-0 flex-1 items-center gap-2">
              <Search size={18} />
              <input
                className="br-control w-full"
                aria-label={t("Search providers")}
                placeholder={t("Search providers")}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>
            <select
              className="br-control"
              aria-label={t("Provider category")}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">{t("All categories")}</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {t(c)}
                </option>
              ))}
            </select>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            {filtered.map((p) => (
              <button
                key={p.id}
                className="rounded-xl border border-border-default p-4 text-left hover:border-accent focus-visible:outline-accent"
                aria-label={`${t("Prepare")} ${p.name}`}
                onClick={() => {
                  setProvider(p);
                  setName(p.name);
                  setSelected([]);
                  setShop("");
                }}
              >
                <div className="flex items-center gap-3">
                  <Badge provider={p} />
                  <div>
                    <h3 className="font-semibold" data-localization="original">
                      {p.name}
                    </h3>
                    <p className="text-xs text-fg-muted">{t(p.category)}</p>
                  </div>
                </div>
                <p className="mt-3 text-sm text-fg-muted">{t(p.purpose)}</p>
                <span className="mt-3 inline-block text-sm font-medium text-accent">
                  {t("Prepare setup")} →
                </span>
              </button>
            ))}
          </div>
          {!filtered.length && (
            <p className="py-8 text-center text-fg-muted">{t("No providers match your search.")}</p>
          )}
          <footer className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border-default pt-4">
            <p className="text-sm text-fg-muted">
              {t("Already have a file? Import items using the existing CSV workflow.")}
            </p>
            <button className="br-btn" onClick={importItems}>
              {t("Import items")}
            </button>
          </footer>
        </>
      ) : (
        <>
          <ol className="my-5 flex flex-wrap gap-3 text-sm">
            {steps.map((label, index) => (
              <li
                key={label}
                aria-current={step === index ? "step" : undefined}
                className="rounded-md bg-surface-muted px-3 py-2"
              >
                {index + 1}. {t(label)}
                {index === step && (
                  <span aria-hidden="true" className="ml-2 text-accent">
                    ●
                  </span>
                )}
              </li>
            ))}
          </ol>
          <p className="mb-5 text-sm text-fg-muted">
            {t(
              "No credentials are needed. This prepares the setup; it does not connect your account.",
            )}
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setError("");
              if (step < 2) setStep(step + 1);
              else {
                const result = save({
                  id: draft?.id || crypto.randomUUID(),
                  provider: provider.id,
                  name: name.trim(),
                  shop: shop.trim(),
                  areas: selected,
                });
                setError(result);
              }
            }}
          >
            {step === 0 && (
              <div className="space-y-4">
                <label className="block text-sm font-medium">
                  {t("Connection name")}
                  <input
                    className="br-control mt-2 w-full"
                    required
                    maxLength={100}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </label>
                <p className="text-sm text-fg-muted">
                  {t("Use a name you recognize, such as DE shop or Main account.")}
                </p>
                {provider.id === "shopify-payments" && (
                  <label className="block text-sm font-medium">
                    {t("Related Shopify shop")}
                    <input
                      className="br-control mt-2 w-full"
                      required
                      maxLength={100}
                      value={shop}
                      onChange={(e) => setShop(e.target.value)}
                    />
                    <span className="mt-2 block text-sm font-normal text-fg-muted">
                      {t("Enter the shop name as planning context. This does not link accounts.")}
                    </span>
                  </label>
                )}
              </div>
            )}
            {step === 1 && (
              <fieldset>
                <legend className="mb-3 text-sm text-fg-muted">
                  {t(
                    "Which data would you like to receive? These are planning choices, not available connector features.",
                  )}
                </legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {provider.areas.map((a) => (
                    <label
                      key={a}
                      className="flex items-center gap-3 rounded-lg border border-border-default p-4"
                    >
                      <input
                        type="checkbox"
                        checked={selected.includes(a)}
                        onChange={(e) =>
                          setSelected(
                            e.target.checked
                              ? [...selected, a]
                              : selected.filter((value) => value !== a),
                          )
                        }
                      />
                      {t(areas[a])}
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
            {step === 2 && (
              <div className="rounded-lg bg-surface-muted p-5">
                <dl className="space-y-4">
                  <div>
                    <dt className="text-sm text-fg-muted">{t("Provider")}</dt>
                    <dd data-localization="original">{provider.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-fg-muted">{t("Connection name")}</dt>
                    <dd className="break-words" data-localization="original">
                      {name.trim()}
                    </dd>
                  </div>
                  {shop && (
                    <div>
                      <dt className="text-sm text-fg-muted">{t("Related Shopify shop")}</dt>
                      <dd className="break-words" data-localization="original">
                        {shop}
                      </dd>
                    </div>
                  )}
                  <div>
                    <dt className="text-sm text-fg-muted">{t("Intended data")}</dt>
                    <dd>{selected.map((a) => t(areas[a])).join(" · ")}</dd>
                  </div>
                </dl>
                <p className="mt-5 text-sm text-fg-muted">
                  {t(
                    "Saved only for you and this company in this browser session. Technical connection follows separately.",
                  )}
                </p>
              </div>
            )}
            {error && (
              <p role="alert" className="mt-4 text-sm text-danger">
                {t(error)}
              </p>
            )}
            <footer className="mt-6 flex justify-between gap-3 border-t border-border-default pt-4">
              <button
                type="button"
                className="br-btn"
                onClick={() => {
                  setError("");
                  if (step > 0) setStep(step - 1);
                  else if (draft) close();
                  else setProvider(undefined);
                }}
              >
                {t(step === 0 && draft ? "Cancel" : "Back")}
              </button>
              <button
                type="submit"
                className="br-btn br-btn-primary"
                disabled={
                  step === 0
                    ? !name.trim() || (provider.id === "shopify-payments" && !shop.trim())
                    : !selected.length
                }
              >
                {t(step === 0 ? "Next" : step === 1 ? "Review" : "Save draft")}
              </button>
            </footer>
          </form>
        </>
      )}
    </dialog>
  );
}
