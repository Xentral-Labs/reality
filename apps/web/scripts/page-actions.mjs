// Page actions render once action discovery has loaded. Checking for the menu right after
// navigation finds nothing, skips the click and leaves every action hidden, so wait for the
// menu first and open it only if it is closed.
export async function openPageActions(page) {
  const summary = page.locator(".register-actions > summary").first();
  await summary.waitFor();
  if (!(await summary.evaluate((node) => node.parentElement.open))) await summary.click();
}
