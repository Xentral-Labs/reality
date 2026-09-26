# Contract: Unsigned Tester Beta

## Package input

The package builder accepts one explicit build-time tester-beta selection. It cannot be
selected by an installed application's command line or environment. The resulting bundle
retains `ai.runreality.local`, declares the immutable `unsigned-tester-beta` channel, and
uses a visible prerelease name and version.

## Custody exchange

The runtime requests both generated installation secrets from exactly one provider selected
by packaged channel metadata. The beta provider returns an installation-bound database
password and vault master key from its private record. The signed provider returns the same
shape from the installation-scoped Keychain coordinates. No response or error may echo values.

## Signed-successor migration

When a valid beta record exists, the signed native shell receives both values over the private
control pipe, writes them to their exact Keychain coordinates and reads both back. It returns
only an installation ID and equality result. Python removes the record only for a successful
exact match. Missing entitlement, denial, interruption, mismatch or partial write starts no
business role and retains the beta installation for recovery.

## Distribution boundary

CI may retain the artifact for authenticated named-test access. A tester beta is invalid input
to tag releases, GitHub pre-releases, public download pages and signed auto-update feeds.
