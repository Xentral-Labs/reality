# UI and API contract
Settings: settings_view=company|personal|access|ai with tenant query. Company create uses POST /api/v1/companies with name and guided_demo=false, then GET /api/v1/bootstrap before exact ID selection. No-company entry uses the same form.
Members use existing GET /api/tenants/{id}/settings/members and POST invitations, invitations/{id}/resend, invitations/{id}/revoke, members/{id}/remove. Review does not call write endpoints. Successful invite means request accepted, not delivered or joined. Unknown result disables retry until successful explicit read. 4xx shows rejected state; business cooldown messages remain visible.
Accept invitation uses existing POST /api/auth/invitations/accept and routes /app?tenant={returned company ID}. No secrets in URLs or logs.
