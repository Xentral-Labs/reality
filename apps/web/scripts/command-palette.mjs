// The global launcher is the command palette inside the [data-action-menu] popover: a typed
// query lists actions as options. Start one by searching for it and choosing its option.
export async function startAction(page, name, query = name) {
  await page.locator("[data-action-launcher] > button").click();
  const palette = page.locator("[data-action-menu]");
  await palette
    .getByRole("combobox", { name: "Search or start an action" })
    .or(palette.getByRole("textbox", { name: "Search or start an action" }))
    .first()
    .fill(query);
  await palette
    .getByRole("option", { name: new RegExp(`^${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) })
    .first()
    .click();
}
