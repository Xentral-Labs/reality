# HTTP

GET /api/company-setup/ai-usage?tenant_id=...&recipient_email=... returns allowance,
self extension availability, can_admin_grant, recipient and grant history.
POST same route accepts tenant_id, request_key, confirmed, mode=self|admin,
questions=20|100, reason, optional recipient_email. Real cookie mandatory.
No actor or remaining-count inputs. Return refreshed usage; invalid/unauthorized
requests use existing domain error mapping.
