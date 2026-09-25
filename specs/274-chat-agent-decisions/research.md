# Research: Chat Agent Decisions

## Reuse the existing confirmation tools

**Decision**: Expose the existing approve/reject tools to ordinary Chat.

**Rationale**: They already enforce exact proposal identity, tenant scope, lifecycle, replay and operation checks.

**Alternatives**: A Chat-specific executor or direct write duplicates rules and weakens traceability.

## Allow the same agent to prepare and settle

**Decision**: A distinct tool call is sufficient; no second identity or user message is required.

**Rationale**: The owner defined proposal then decision as the safety boundary.

**Alternatives**: Requiring another agent or person adds an unrequested restriction.

## Persist Chat settlement on the decision

**Decision**: Add one observed settlement-channel field.

**Rationale**: Decisions currently distinguish person, MCP token or unknown. Interaction rows know `chat` but expire and are not durable authority.

**Alternatives**: `actor_type=agent` describes the proposer and can be followed by a person; joining expiring telemetry decays; using the browser user fabricates personal approval.

## Keep protected authority separate

**Decision**: Do not pass the browser user as confirming principal. Owner/person-only actions remain refused to generic Chat.

**Rationale**: Reality observes the model's call, not a personal approval. Confirmation access is not domain authority.

## Carry channel in server context

**Decision**: The Chat adapter sets settlement context internally, like MCP token context.

**Rationale**: The model must not be able to forge attribution through tool arguments.

## Correct generic human-only wording

**Decision**: Generic confirmation guidance says authorized decision, while genuinely owner/person-specific operations keep their stricter wording.

**Rationale**: Prompt, catalog and runtime semantics must agree.
