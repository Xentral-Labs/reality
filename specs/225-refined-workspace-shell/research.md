# Design research

- Decision: Keep the existing 200px/60px navigation widths and chat breakpoints.
  Rationale: The approved concept concerns hierarchy; widths already support dense work.
  Alternative: Widen all navigation, rejected as unnecessary layout churn.
- Decision: Full-height desktop sidebar and side chat, with a content-only 48px header.
  Rationale: Removes the continuous utility strip and aligns working surfaces.
  Alternative: Merely shrink the global bar, rejected because mixed context remains.
- Decision: Use native popovers for sidebar menus and description disclosure.
  Rationale: Escape, focus restoration and top-layer rendering avoid scroll clipping.
  Alternative: Absolute menus in scrolling sidebar, rejected due to clipping.
- Decision: Keep business content typography; refine shell/navigation/tabs only.
  Rationale: A small coherent first step preserves operational readability.
