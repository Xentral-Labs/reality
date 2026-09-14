# Research

Existing `api.updateProfile` PUT requires display_name/language/locale/timezone and returns AuthUser. AuthGate updateUser remembers language; LocalizationProvider consumes the returned account. `web/auth.py` validates IANA zone with ZoneInfo and trims name. Personal settings require no business proposal.

`APIError.status` distinguishes client rejection from network/5xx uncertainty. Recovery is GET auth/me with four-field comparison; no retrying PUT automatically. Profile updates are existing last-save semantics, not revision guarded.

`services/memberships.py` requires owner membership even for platform admins. Its GET may expire invitations, and returns at most500 in each list, no totals. AI owner guard permits platform-admin bypass, but conservative owner-only presentation does not alter backend access. `copilot.available` means configured credentials, not provider health. `provider_name` is hardcoded and unsuitable for arbitrary company presets; render mode and model only.

Theme helpers already support system changes but unified header lacks subscription and resolves system incorrectly. Reuse helpers plus event; no parallel theme authority. Supporting company settings chooses tabs in local React state, so link to its company root rather than inventing a tab query contract.

Decision: no new backend, dependencies, schema, admin mutation UI or source/evidence model. Research completed by finance_read_audit and reviewed against callers and services.

Access summary retains the canonical pending/expired invitation filter. Delivery states are pending, processing, delivered, retry and failed; labels are localized and distinct from the invitation state.
