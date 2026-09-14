# Presentation Model

No business persistence changes. Categories contain stable keys, labels and ordered
subgroups. Each canonical Command service maps to one subgroup. Workspace Actions
inherit their Command subgroup. Launch entries contain stable key, label, command,
existing form identity or internal navigation target, and explicit placement contexts.
Unknown commands/groups, duplicate identities and absent primary paths fail validation.
Runtime unknown capability entries remain visible under Unclassified.
