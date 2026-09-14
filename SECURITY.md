# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security problems.

Use GitHub's private vulnerability reporting: open the **Security** tab of this repository and
choose **Report a vulnerability**. The report reaches the maintainers only. If that path is not
available to you, write to `support@xentral.com` with "Reality security" in the subject.

Include what you found, how to reproduce it, the version or commit you tested (the App reports
both under `GET /api/v1/system/status`), and what impact you believe it has.

## What to expect

- An acknowledgement within five working days.
- A fix or a documented mitigation for confirmed issues in the next release, sooner for anything
  that exposes tenant data across companies or bypasses authentication.
- Credit in the release notes if you want it.

## Scope

Reality is tenant-scoped by design: every business table and every service query carries a tenant
boundary, and cross-tenant reads behave as not found. Anything that lets one company see or change
another company's data, that bypasses sign-in, confirmation of mutating chat actions or MCP token
scopes, or that leaks stored credentials, is in scope and treated as critical.

Self-hosted installations are operated by their owners. Configuration mistakes on a specific
installation (open ports, weak passwords, missing HTTPS) are not vulnerabilities in Reality, but
if the installer or the documentation led you into one, please report that too.

## Supported versions

Security fixes land on `main` and in the next tagged release. Self-hosted operators should stay on
the latest release; `./reality.sh upgrade` does that with one command.
