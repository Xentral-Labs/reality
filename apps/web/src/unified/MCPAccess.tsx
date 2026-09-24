import { useEffect, useState } from "react";
import { type AIConfiguration } from "../api";
import { formatDateTime, t } from "../localization";
export const accessLabel = (access: string) =>
  t(
    (
      { read: "Read", propose: "Prepare changes", confirm: "Approve and execute" } as Record<
        string,
        string
      >
    )[access] || access,
  );
export function MCPAccess({
  data,
  disabled,
  revision,
  create,
  revoke,
}: {
  data: AIConfiguration;
  disabled: boolean;
  revision: number;
  create: (name: string, tools: string[]) => void;
  revoke: (token: AIConfiguration["tokens"][number]) => void;
}) {
  const [creating, setCreating] = useState(false),
    [name, setName] = useState(""),
    [selected, setSelected] = useState<string[]>([]),
    [query, setQuery] = useState(""),
    [toolPage, setToolPage] = useState(1),
    [tokenPage, setTokenPage] = useState(1),
    [copyError, setCopyError] = useState(false);
  useEffect(() => {
    setCreating(false);
    setName("");
    setSelected([]);
  }, [revision]);
  const tools = data.tools || [],
    tokens = data.tokens || [];
  const filtered = tools.filter((tool) =>
    `${tool.label} ${tool.name} ${tool.description}`.toLowerCase().includes(query.toLowerCase()),
  );
  const page = Math.min(tokenPage, Math.max(1, Math.ceil(tokens.length / 25)));
  return (
    <details open data-mcp-access className="rounded-lg border border-border-default p-4 sm:p-5">
      <summary className="cursor-pointer font-semibold">{t("External agents · MCP")}</summary>
      <div className="mt-5 space-y-5">
        <p className="text-sm text-fg-muted">
          {t(
            "MCP tokens give external agents access to this company. Permissions apply to the selected tools.",
          )}
        </p>
        <div className="space-y-2">
          <p className="text-sm font-medium">{t("MCP endpoint")}</p>
          <code className="block break-all text-xs">{data.mcp_url}</code>
          <button
            className="br-btn"
            disabled={!data.mcp_url}
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(data.mcp_url);
                setCopyError(false);
              } catch {
                setCopyError(true);
              }
            }}
          >
            {t("Copy URL")}
          </button>
          {copyError && (
            <p role="alert" className="text-sm">
              {t("Copy failed. Select and copy the value manually.")}
            </p>
          )}
        </div>
        <p className="text-sm text-fg-muted">
          {t(
            "Tokens remain active until revoked. Removing an owner's membership does not revoke their company tokens.",
          )}
        </p>
        <button className="br-btn" disabled={disabled} onClick={() => setCreating(true)}>
          {t("New MCP token")}
        </button>
        {creating && (
          <form
            className="space-y-4 rounded-lg bg-surface-muted p-4"
            onSubmit={(e) => {
              e.preventDefault();
              create(name.trim(), selected);
            }}
          >
            <fieldset disabled={disabled} className="min-w-0 space-y-4">
              <label className="block text-sm">
                {t("Token name")}
                <input
                  className="br-control mt-2 w-full"
                  required
                  maxLength={100}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </label>
              <p className="text-sm">
                {t("Choose exact tools. No permissions are selected by default.")}
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className="br-btn"
                  onClick={() =>
                    setSelected(
                      tools.filter((tool) => tool.access === "read").map((tool) => tool.name),
                    )
                  }
                >
                  {t("Select read tools")}
                </button>
                <button
                  type="button"
                  className="br-btn"
                  onClick={() => setSelected([...new Set(tools.map((tool) => tool.name))])}
                >
                  {t("Select full access")}
                </button>
                <button type="button" className="br-btn" onClick={() => setSelected([])}>
                  {t("Clear selection")}
                </button>
                <span className="self-center text-sm">
                  {selected.length} {t("selected tools")}
                </span>
              </div>
              <label className="block text-sm">
                {t("Search tools")}
                <input
                  className="br-control mt-2 w-full"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setToolPage(1);
                  }}
                />
              </label>
              <div className="max-h-80 space-y-2 overflow-auto">
                {filtered.slice((toolPage - 1) * 25, toolPage * 25).map((tool) => (
                  <label
                    key={tool.name}
                    className="flex items-start gap-3 rounded-lg border border-border-default bg-surface p-3"
                  >
                    <input
                      type="checkbox"
                      className="mt-1"
                      aria-label={t(tool.label)}
                      checked={selected.includes(tool.name)}
                      onChange={(e) =>
                        setSelected(
                          e.target.checked
                            ? [...selected, tool.name]
                            : selected.filter((value) => value !== tool.name),
                        )
                      }
                    />
                    <span className="min-w-0">
                      <strong className="block break-words text-sm">{t(tool.label)}</strong>
                      <code className="block break-all text-xs text-fg-muted">{tool.name}</code>
                      <span className="block text-xs">{accessLabel(tool.access)}</span>
                      <span className="block break-words text-xs text-fg-muted">
                        {t(tool.description)}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
              {!filtered.length && <p>{t("No matching tools.")}</p>}
              {filtered.length > 25 && (
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    className="br-btn"
                    disabled={toolPage === 1}
                    onClick={() => setToolPage(toolPage - 1)}
                  >
                    {t("Previous")}
                  </button>
                  <span>
                    {toolPage} / {Math.ceil(filtered.length / 25)}
                  </span>
                  <button
                    type="button"
                    className="br-btn"
                    disabled={toolPage * 25 >= filtered.length}
                    onClick={() => setToolPage(toolPage + 1)}
                  >
                    {t("Next")}
                  </button>
                </div>
              )}
              <div className="flex flex-wrap gap-3">
                <button
                  className="br-btn br-btn-primary"
                  disabled={!name.trim() || !selected.length}
                >
                  {t("Review token")}
                </button>
                <button type="button" className="br-btn" onClick={() => setCreating(false)}>
                  {t("Close")}
                </button>
              </div>
            </fieldset>
          </form>
        )}
        <h3 className="font-semibold">{t("Active MCP tokens")}</h3>
        {!tokens.length && <p className="text-sm text-fg-muted">{t("No active MCP tokens.")}</p>}
        {tokens.slice((page - 1) * 25, page * 25).map((token) => (
          <article
            data-token-id={token.id}
            key={token.id}
            className="space-y-3 rounded-lg border border-border-default p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h4 className="break-words font-medium">{token.name}</h4>
                <p className="break-all text-xs text-fg-muted">{token.id}</p>
                <code className="break-all text-xs">{token.token_prefix}…</code>
              </div>
              <button className="br-btn" disabled={disabled} onClick={() => revoke(token)}>
                {t("Revoke")}
              </button>
            </div>
            <p className="text-xs text-fg-muted">
              {t("Created")}: {formatDateTime(token.created_at)} · {t("Last used")}:{" "}
              {token.last_used_at ? formatDateTime(token.last_used_at) : t("Never")}
            </p>
            <details>
              <summary className="cursor-pointer text-sm">
                {token.allowed_tools.includes("*")
                  ? t("All current and future tools")
                  : `${token.allowed_tools.length} ${t("selected tools")}`}
              </summary>
              <ul className="mt-2 max-h-48 space-y-1 overflow-auto text-xs">
                {token.allowed_tools.map((tool) => (
                  <li className="break-all" key={tool}>
                    {tool} ·{" "}
                    {tool === "*"
                      ? t("Includes approval and execution")
                      : accessLabel(tools.find((row) => row.name === tool)?.access || "Unknown")}
                  </li>
                ))}
              </ul>
            </details>
          </article>
        ))}
        {tokens.length > 25 && (
          <div className="flex items-center gap-3">
            <button className="br-btn" disabled={page === 1} onClick={() => setTokenPage(page - 1)}>
              {t("Previous")}
            </button>
            <span>
              {page} / {Math.ceil(tokens.length / 25)}
            </span>
            <button
              className="br-btn"
              disabled={page * 25 >= tokens.length}
              onClick={() => setTokenPage(page + 1)}
            >
              {t("Next")}
            </button>
          </div>
        )}
      </div>
    </details>
  );
}
