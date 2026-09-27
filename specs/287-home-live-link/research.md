# Research: Home Live Link Placement

## Decision: place the action beside the Live status

**Rationale**: The status explains what is live and the action opens the detailed live monitor. Grouping them provides the shortest semantic and visual relationship, while leaving the time-range selector responsible only for graph range.

**Alternatives considered**:

- Keep the outlined button below the selector: rejected because it creates an unrelated second row.
- Put the button before the period selector: rejected because it still mixes navigation with filtering.
- Make the word "Live" itself the action: rejected because it would blur passive status with navigation and reduce clarity for users without access.

## Decision: preserve navigation ownership in HomePulse

**Rationale**: `HomePulse` already receives the permission-dependent callback. Passing a React node to the graph keeps routing and authorization out of the graph component.

**Alternatives considered**:

- Give `ActivityGraph` the callback and construct the button there: rejected because it makes a data-visualization component own a product navigation concern.

