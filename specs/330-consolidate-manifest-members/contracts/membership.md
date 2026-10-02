# Manifest Membership Compatibility Contract

All five original SQL resource names retain exactly their original columns, types and supported INSERT/UPDATE/DELETE/RETURNING behavior. Original ORM member IDs are caller supplied and remain unchanged. Inserts route to a closed family internally; callers do not supply another family. Wrong tenant, missing parent/target, duplicate family selection or inconsistent physical shape is refused by persistence constraints. The same opaque ID remains valid across distinct families and tenants.

Existing receipt services, tools, record-detail resources, child pagination, confirmation, permissions and error codes remain unchanged. Member hashing retains original family keys and sorted selected target IDs. New decisions cannot change a historical review. Current direct member-loss corruption testing remains supported and must still produce the existing read refusal; no new immutable-member guard is introduced.

Schema inspection must honestly distinguish physical store and compatibility views. Tenant counts/purge visit physical members once. Downgrade restores original physical member tables and their exact DDL/index contracts, including supported post-upgrade changes. This contract changes no UI, command schema or live deployment behavior.
