# Research

Decision: remove the legacy company_insights service and GET reads. Repository
reference search found only Overview/Home consumers and feature tests. The
composable analytics contributor API uses POST /analytics/query/contributors and remains independent.
Alternative: keep a hidden Overview backend. Rejected because the user explicitly
requested removing its backend too. Keep Home navigation as a simple existing CTA.
