# Public Site UI Contract

## Shared navigation

- Every public page exposes `https://github.com/Xentral-Labs/reality`.
- The entry is labelled as an open-source/GitHub destination and coexists with Overview, How it works, Packages, language, sign-in, and account creation.
- Desktop and mobile navigation expose the same destination.

## Landing-page section

- One open-source section appears after the autonomy narrative and before the final account CTA.
- It states that visitors may inspect the model, principles, implementation, and progress.
- The primary action opens the canonical repository; the secondary action opens the configured Docs root.
- All new copy is localized in English, German, Dutch, and Spanish.

## Boundary

- Rendering makes no network request to GitHub or Docs.
- No new route, business state, tenant state, or authentication state is introduced.
