# Apple Developer ID Release Setup

Use this runbook when the Apple Developer Program membership is active. It completes
the credentialed gates in T013, T016 and T017. Never commit or paste a certificate,
private key, password, provisioning profile or encoded secret into an issue, pull
request, log or chat.

Official references:

- [Create Developer ID certificates](https://developer.apple.com/help/account/certificates/create-developer-id-certificates)
- [App Store Connect API access](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api)
- [Create App Store Connect API keys](https://developer.apple.com/documentation/AppStoreConnectAPI/creating-api-keys-for-app-store-connect-api)
- [Notarizing macOS software](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)

## 1. Confirm membership and authority

Sign in to Apple Developer with the intended owner account. Membership must show
**Apple Developer Program — Active**. Creating a Developer ID certificate normally
requires the Account Holder role. Team API-key and profile management require the
roles Apple lists in the linked documentation.

Record the ten-character Team ID shown on the membership page. It becomes the GitHub
secret `APPLE_TEAM_ID`; it is an identifier, not a private key.

## 2. Register the application identifier

In **Certificates, Identifiers & Profiles → Identifiers**, register an explicit macOS
App ID with bundle identifier `ai.runreality.local`. Enable the Keychain capability
needed for the installation-scoped access group. Do not substitute a wildcard App ID
or change the bundle identifier: installed data and Keychain coordinates depend on it.

## 3. Create and install the Developer ID Application certificate

On the signing Mac, open **Keychain Access → Certificate Assistant → Request a
Certificate From a Certificate Authority**. Enter the developer-account email and a
recognizable common name, select **Saved to disk**, and save the CSR.

In **Certificates, Identifiers & Profiles → Certificates → +**, choose
**Developer ID Application** (not Developer ID Installer, Apple Distribution or Mac
App Distribution), upload the CSR, generate the certificate and download the `.cer`.
Double-click it. In Keychain Access under **login → My Certificates**, expanding the
certificate must show its private key.

Verify the installed identity without exposing key material:

```sh
security find-identity -v -p codesigning
```

The full displayed identity, for example
`Developer ID Application: Example GmbH (ABCDE12345)`, becomes
`APPLE_SIGNING_IDENTITY`.

## 4. Export the signing identity

In Keychain Access, select the Developer ID Application certificate together with its
private key and export it as a password-protected `.p12`. Use a new strong password.
The `.p12` becomes `APPLE_CERTIFICATE_P12`; its export password becomes
`APPLE_CERTIFICATE_PASSWORD`.

Encode the file locally for GitHub without printing it:

```sh
base64 -i DeveloperIDApplication.p12 | pbcopy
```

Paste the clipboard only into the corresponding GitHub Actions secret, then remove the
exported `.p12` from ordinary folders after confirming the protected backup policy.

## 5. Create the Developer ID provisioning profile

In **Certificates, Identifiers & Profiles → Profiles → +**, choose the Developer ID
distribution profile for macOS, select the explicit `ai.runreality.local` App ID and
the Developer ID Application certificate, name the profile clearly and download it.
The profile must authorize the application identifier and its private Keychain access
group. Do not use a development, Mac App Store or wildcard profile.

Inspect it locally before upload:

```sh
security cms -D -i Reality_Local.provisionprofile > /tmp/reality-profile.plist
/usr/libexec/PlistBuddy -c 'Print :Entitlements:application-identifier' /tmp/reality-profile.plist
/usr/libexec/PlistBuddy -c 'Print :Entitlements:keychain-access-groups' /tmp/reality-profile.plist
```

The application identifier must be `<TEAM_ID>.ai.runreality.local`, and the Keychain
group must contain the same exact value. Encode the original profile with
`base64 -i Reality_Local.provisionprofile | pbcopy`; store it as
`APPLE_PROVISIONING_PROFILE`.

## 6. Create a team App Store Connect API key

In **App Store Connect → Users and Access → Integrations → App Store Connect API**,
request API access first if Apple still requires approval. Create a **team API key**
with the least role that permits notarization. Do not use an individual API key:
Apple documents that individual keys cannot use `notarytool`.

Download the `.p8` exactly once and record its Key ID and Issuer ID:

- Key ID → `APPLE_API_KEY_ID`
- Issuer ID → `APPLE_API_ISSUER_ID`
- `base64 -i AuthKey_<KEY_ID>.p8 | pbcopy` → `APPLE_API_PRIVATE_KEY`

Keep the original `.p8` in approved secret storage. Revoke it immediately if exposed.

## 7. Add the eight GitHub Actions secrets

In the GitHub repository, open **Settings → Secrets and variables → Actions → New
repository secret** and create exactly:

- `APPLE_CERTIFICATE_P12`
- `APPLE_CERTIFICATE_PASSWORD`
- `APPLE_SIGNING_IDENTITY`
- `APPLE_TEAM_ID`
- `APPLE_PROVISIONING_PROFILE`
- `APPLE_API_KEY_ID`
- `APPLE_API_ISSUER_ID`
- `APPLE_API_PRIVATE_KEY`

The workflow deliberately treats a partial set as unsigned and refuses publication.

## 8. Run the non-publishing credentialed qualification first

Open **Actions → macOS release → Run workflow** and use:

- `version`: a new prerelease version such as `0.2.0-rc.1`
- `tester_beta`: `false`
- `publish`: `false`

Do not create a release tag yet. The workflow must pass nested signing, entitlement
verification, notarization, stapling, Gatekeeper assessment, reproducibility comparison
and checksum generation. Retain the workflow URL and artifact manifest in
`verification.md` without copying secret values.

On a disposable clean supported Mac, download the artifact and complete T013/T017:
first launch, Keychain creation, ten restart cycles, backup/restore, full erasure and
offline Gatekeeper validation. A former unsigned beta installation must migrate the
two exact generated custody values before deleting its local custody record.

## 9. Publish only after qualification

After every required gate is recorded green, create the version tag in the form
`mac-v0.2.0`. The workflow creates or updates the GitHub pre-release. Never set
`tester_beta: true` for a tag or publication request; CI rejects that combination.

If any credential, entitlement, notarization or clean-Mac check fails, do not weaken
the workflow. Rotate or correct the Apple material, increment the version when needed,
and repeat the non-publishing qualification.
