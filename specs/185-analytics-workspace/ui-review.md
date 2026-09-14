# Reports workspace — product review

Status: approved design, implemented in the integrated Analytics workspace. The
[wireframe](workspace-wireframe.svg) remains the original illustrative design rather
than business data. Browser verification uses desktop/mobile screenshots and all four
supported languages; results are recorded in `verification.md`.

## Placement and hierarchy

Use the existing Analytics → Reports destination. Do not add a second primary navigation entry. Keep the application sidebar and existing global Ask Reality dock.

Three local tabs:

- **Overview**: existing operational observations and their contributor links, plus entry points into editable starter reports. Old metric/day links continue here.
- **Explore**: visual configuration and one focused analysis. The initial empty explorer offers starter examples and a blank report; it never displays invented sample results.
- **My reports**: search and reopen the current user's company-scoped saved definitions; explicit rename, duplicate and delete actions.

## Explore composition

Header: report title, unsaved/changed indicator, Discuss in chat, Export and Save. Export is unavailable until a valid result exists. Save changes the definition, not its result.

Below it: compact dataset/date/timezone/comparison controls. The collapsible left configuration panel contains filters, measures, grouping and ordering. Entity pickers use scoped business labels. Advanced AND/OR filters are available without taking over the first-use screen.

The result takes the remaining width. Its first row states the executed measure and period, followed by Table / Chart / Pivot selection. A bar chart compares categories; a line chart requires a date grouping. Incompatible chart options explain their requirement. Pivot exposes rows, columns and measures with explicit limits.

The result table has aligned numeric columns, visible units/currencies, sorting and contributor actions. The observation footer states retained-data scope, known exclusions and the observation time. Detailed definitions are expandable. No SQL editor, ORM field names or technical diagnostics appear in the main flow.

## Key interactions

1. Choose a starter or dataset, date window and measure. Add product/customer filters or grouping.
2. Run explicitly. While the draft changes, the current result keeps its executed definition and a “Changes not applied” indicator.
3. Change Table/Chart/Pivot presentation without changing the business question. Population totals and distinct totals come from the shared execution capability.
4. Select a value to open its contributors, then an existing Inspector record. Closing it restores the report and scroll context.
5. Save explicitly with a name. My reports retains definitions only. Reruns show current observation time and newly resolved relative dates.
6. Discuss in chat passes this definition to the existing dock. Agent-produced reports offer Open in Reports. There is no new inline chat input pretending to provide a separate assistant.

## Layout and states

- At wide desktop widths: roughly 260px collapsible configuration beside results, within the existing shell. When the global chat is open, collapse configuration if needed rather than squeezing the table beyond usability.
- On mobile: configuration opens as a labelled drawer/section; results occupy the page. Tables scroll within their own region, while controls and explanations fit the viewport.
- Loading preserves the executed result label. Errors do not replace old results with zero. Cancellation stops the run; late responses cannot override a newer definition/company.
- Empty results distinguish no matches from unknown/missing data. Oversized charts offer a labelled subset or table, never an unlabeled truncated total.
- Keyboard users can configure filters, run, switch views and open/close contributors with focus restored. Chart values also exist in the table.

## Scope-review decisions

The proposal includes pivot, private saved definitions, CSV and chat handoff as part of the completed feature, with basic query execution and visual exploration delivered first. Shared report editing, scheduled delivery and a multi-tile dashboard designer are deferred. All 30 assessed questions receive either the supported result or the explicitly restricted answer in the coverage contract.

This file is product interaction design only. Technical architecture, schema and implementation tasks remain gated on product-scope acceptance under the repository workflow.
