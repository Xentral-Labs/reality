use base64::Engine;
use security_framework::passwords::{
    delete_generic_password_options, generic_password, set_generic_password_options,
    PasswordOptions,
};
use security_framework::random::SecRandom;
use security_framework_sys::base::errSecItemNotFound;

const DATABASE_PURPOSE: &str = "database";
const VAULT_PURPOSE: &str = "vault";

#[derive(Debug, PartialEq, Eq)]
pub struct Coordinates {
    pub service: String,
    pub account: String,
}

pub struct InstallationSecrets {
    pub database_password: String,
    pub vault_master_key: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum InstallationSecretState {
    Present,
    Missing,
    Partial,
}

pub fn coordinates(bundle: &str, installation: &str, purpose: &str) -> Result<Coordinates, String> {
    if bundle.trim().is_empty() || installation.trim().is_empty() {
        return Err("Bundle and installation identities are required".into());
    }
    if ![DATABASE_PURPOSE, VAULT_PURPOSE].contains(&purpose) {
        return Err("Unknown Reality Local Keychain purpose".into());
    }
    Ok(Coordinates {
        service: format!("{bundle}.{purpose}"),
        account: installation.into(),
    })
}

fn random_bytes(length: usize) -> Result<Vec<u8>, String> {
    let mut value = vec![0; length];
    SecRandom::default()
        .copy_bytes(&mut value)
        .map_err(|error| format!("Keychain randomness failed: {error}"))?;
    Ok(value)
}

fn database_password() -> Result<String, String> {
    Ok(random_bytes(32)?
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect())
}

fn vault_master_key() -> Result<String, String> {
    Ok(base64::engine::general_purpose::URL_SAFE.encode(random_bytes(32)?))
}

fn options(coordinates: &Coordinates) -> PasswordOptions {
    let mut value =
        PasswordOptions::new_generic_password(&coordinates.service, &coordinates.account);
    value.use_protected_keychain();
    value
}

fn get_or_create(
    coordinates: &Coordinates,
    create: impl FnOnce() -> Result<String, String>,
) -> Result<String, String> {
    let options = || {
        let mut value =
            PasswordOptions::new_generic_password(&coordinates.service, &coordinates.account);
        value.use_protected_keychain();
        value
    };
    match generic_password(options()) {
        Ok(value) => String::from_utf8(value).map_err(|_| "Keychain value is not UTF-8".into()),
        Err(error) if error.code() == errSecItemNotFound => {
            let value = create()?;
            set_generic_password_options(value.as_bytes(), options())
                .map_err(|error| format!("Keychain write failed: {error}"))?;
            let read_back = generic_password(options())
                .map_err(|error| format!("Keychain verification failed: {error}"))?;
            if read_back != value.as_bytes() {
                return Err("Keychain verification returned a different value".into());
            }
            Ok(value)
        }
        Err(error) => Err(format!("Keychain read failed: {error}")),
    }
}

pub fn installation_secrets(
    bundle: &str,
    installation: &str,
    legacy_database_password: Option<&str>,
) -> Result<InstallationSecrets, String> {
    let database = coordinates(bundle, installation, DATABASE_PURPOSE)?;
    let vault = coordinates(bundle, installation, VAULT_PURPOSE)?;
    Ok(InstallationSecrets {
        database_password: get_or_create(&database, || {
            legacy_database_password
                .map(str::to_owned)
                .map(Ok)
                .unwrap_or_else(database_password)
        })?,
        vault_master_key: get_or_create(&vault, vault_master_key)?,
    })
}

pub fn migrate_installation_secrets(
    bundle: &str,
    installation: &str,
    database_password: &str,
    vault_master_key: &str,
) -> Result<(), String> {
    for (purpose, expected) in [
        (DATABASE_PURPOSE, database_password),
        (VAULT_PURPOSE, vault_master_key),
    ] {
        let location = coordinates(bundle, installation, purpose)?;
        let actual = get_or_create(&location, || Ok(expected.to_owned()))?;
        if actual.as_bytes() != expected.as_bytes() {
            return Err(format!(
                "Existing {purpose} Keychain value does not match beta custody"
            ));
        }
    }
    Ok(())
}

pub fn delete_installation_secrets(bundle: &str, installation: &str) -> Result<(), String> {
    // Both entries must exist before the first destructive operation begins.
    let owned = [
        coordinates(bundle, installation, DATABASE_PURPOSE)?,
        coordinates(bundle, installation, VAULT_PURPOSE)?,
    ];
    for location in &owned {
        generic_password(options(location))
            .map_err(|error| format!("Keychain erasure preflight failed: {error}"))?;
    }
    for location in &owned {
        delete_generic_password_options(options(location))
            .map_err(|error| format!("Keychain erasure failed: {error}"))?;
    }
    for location in &owned {
        match generic_password(options(location)) {
            Err(error) if error.code() == errSecItemNotFound => {}
            Err(error) => return Err(format!("Keychain erasure verification failed: {error}")),
            Ok(_) => return Err("Keychain erasure verification found a retained value".into()),
        }
    }
    Ok(())
}

pub fn installation_secret_state(
    bundle: &str,
    installation: &str,
) -> Result<InstallationSecretState, String> {
    let mut present = 0;
    for purpose in [DATABASE_PURPOSE, VAULT_PURPOSE] {
        let location = coordinates(bundle, installation, purpose)?;
        match generic_password(options(&location)) {
            Ok(_) => present += 1,
            Err(error) if error.code() == errSecItemNotFound => {}
            Err(error) => return Err(format!("Keychain erasure inspection failed: {error}")),
        }
    }
    Ok(match present {
        0 => InstallationSecretState::Missing,
        2 => InstallationSecretState::Present,
        _ => InstallationSecretState::Partial,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn coordinates_are_exact_and_installation_scoped() {
        assert_eq!(
            coordinates("ai.runreality.local", "opaque-installation", "vault").unwrap(),
            Coordinates {
                service: "ai.runreality.local.vault".into(),
                account: "opaque-installation".into(),
            }
        );
        assert!(coordinates("ai.runreality.local", "opaque-installation", "other").is_err());
    }

    #[test]
    fn generated_values_have_the_required_shapes() {
        let database = database_password().unwrap();
        let vault = vault_master_key().unwrap();
        assert_eq!(database.len(), 64);
        assert!(database.bytes().all(|byte| byte.is_ascii_hexdigit()));
        assert_eq!(vault.len(), 44);
        assert!(vault.ends_with('='));
    }

    #[test]
    fn erasure_coordinates_cover_only_the_selected_installation() {
        let selected_database =
            coordinates("ai.runreality.local", "selected", DATABASE_PURPOSE).unwrap();
        let selected_vault = coordinates("ai.runreality.local", "selected", VAULT_PURPOSE).unwrap();
        let sibling = coordinates("ai.runreality.local", "sibling", VAULT_PURPOSE).unwrap();

        assert_eq!(selected_database.account, "selected");
        assert_eq!(selected_vault.account, "selected");
        assert_ne!(selected_vault, sibling);
        assert_ne!(selected_database.service, selected_vault.service);
    }

    #[test]
    #[ignore = "requires an unlocked macOS login Keychain"]
    fn keychain_round_trip_is_exact_and_does_not_replace_an_existing_value() {
        let installation = format!(
            "reality-local-test-{}-{:?}",
            std::process::id(),
            std::time::SystemTime::now()
        );
        let location = coordinates("ai.runreality.local.test", &installation, "vault").unwrap();
        let first = get_or_create(&location, || Ok("first-value".into())).unwrap();
        let second = get_or_create(&location, || Ok("replacement".into())).unwrap();
        assert_eq!(first, "first-value");
        assert_eq!(second, "first-value");
        let mut options =
            PasswordOptions::new_generic_password(&location.service, &location.account);
        options.use_protected_keychain();
        delete_generic_password_options(options).unwrap();
        let mut options =
            PasswordOptions::new_generic_password(&location.service, &location.account);
        options.use_protected_keychain();
        assert_eq!(
            generic_password(options).unwrap_err().code(),
            errSecItemNotFound
        );
    }

    #[test]
    #[ignore = "requires an unlocked macOS login Keychain"]
    fn erasure_removes_both_owned_entries_and_preserves_a_sibling() {
        let bundle = "ai.runreality.local.test";
        let selected = format!("selected-{}", std::process::id());
        let sibling = format!("sibling-{}", std::process::id());
        installation_secrets(bundle, &selected, None).unwrap();
        installation_secrets(bundle, &sibling, None).unwrap();

        delete_installation_secrets(bundle, &selected).unwrap();

        for purpose in [DATABASE_PURPOSE, VAULT_PURPOSE] {
            let selected_location = coordinates(bundle, &selected, purpose).unwrap();
            assert_eq!(
                generic_password(options(&selected_location))
                    .unwrap_err()
                    .code(),
                errSecItemNotFound
            );
            let sibling_location = coordinates(bundle, &sibling, purpose).unwrap();
            assert!(generic_password(options(&sibling_location)).is_ok());
            delete_generic_password_options(options(&sibling_location)).unwrap();
        }
    }
}
