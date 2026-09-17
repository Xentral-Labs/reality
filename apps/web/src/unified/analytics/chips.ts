/** A chosen chip has to look chosen.
 *
 * `br-btn` carries no pressed state of its own outside the tab strips, so a
 * toggle built from it reads as unselected however many times it is pressed.
 * The accent is added here rather than in the stylesheet so that every other
 * `aria-pressed` button in the application keeps the look it has today.
 */
const PICKED = "border-accent bg-accent-soft text-fg-strong";

export function chip(picked: boolean) {
  return `br-btn ${picked ? PICKED : ""}`.trimEnd();
}
