use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::Manager;

mod keychain;

struct Probe(Mutex<Child>);
impl Drop for Probe {
    fn drop(&mut self) {
        if let Ok(child) = self.0.get_mut() {
            drop(child.stdin.take());
            stop_child(child);
        }
    }
}

fn stop_child(child: &mut Child) {
    drop(child.stdin.take());
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(45);
    while std::time::Instant::now() < deadline {
        if matches!(child.try_wait(), Ok(Some(_))) {
            return;
        }
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
    let _ = child.kill();
    let _ = child.wait();
}
fn default_cookie() -> String {
    "reality_native_probe".into()
}
fn default_path() -> String {
    "/".into()
}

#[derive(serde::Deserialize)]
struct Endpoint {
    origin: String,
    token: String,
    #[serde(default = "default_cookie")]
    cookie_name: String,
    #[serde(default = "default_path")]
    path: String,
}

#[derive(serde::Deserialize)]
struct KeychainRequest {
    kind: String,
    installation_id: String,
    legacy_database_password: Option<String>,
}

#[derive(serde::Serialize)]
struct KeychainResponse {
    kind: &'static str,
    installation_id: String,
    database_password: String,
    vault_master_key: String,
}

#[derive(serde::Deserialize)]
struct KeychainErasureRequest {
    kind: String,
    installation_id: String,
    operation: String,
}

#[derive(serde::Serialize)]
struct KeychainErasureResponse {
    kind: &'static str,
    installation_id: String,
    state: &'static str,
}

#[derive(serde::Deserialize)]
struct BetaCustodyRequest {
    kind: String,
    installation_id: String,
}

#[derive(serde::Serialize)]
struct BetaCustodyResponse {
    kind: &'static str,
    installation_id: String,
}

#[derive(serde::Deserialize)]
struct KeychainMigrationRequest {
    kind: String,
    installation_id: String,
    database_password: String,
    vault_master_key: String,
}

#[derive(serde::Serialize)]
struct KeychainMigrationResponse {
    kind: &'static str,
    installation_id: String,
    exact: bool,
}

type Setup = Box<dyn std::error::Error>;

fn maintenance_arguments(arguments: &[String]) -> Result<Vec<String>, Setup> {
    let mut forwarded = Vec::new();
    let mut operation: Option<&str> = None;
    let mut confirmed = false;
    let mut index = 0;
    while index < arguments.len() {
        match arguments[index].as_str() {
            "--backup" | "--restore" => {
                let name = arguments[index].as_str();
                if operation.is_some() {
                    return Err("Choose either backup or restore, not both".into());
                }
                let path = arguments.get(index + 1).ok_or("Missing maintenance path")?;
                operation = Some(name);
                forwarded.push(name.to_owned());
                forwarded.push(path.to_owned());
                index += 2;
            }
            "--confirm-restore" => {
                confirmed = true;
                forwarded.push(arguments[index].clone());
                index += 1;
            }
            "--erase" => {
                if operation.is_some() {
                    return Err("Choose exactly one maintenance operation".into());
                }
                operation = Some("--erase");
                forwarded.push(arguments[index].clone());
                index += 1;
            }
            "--confirm-erasure" => {
                forwarded.push(arguments[index].clone());
                index += 1;
            }
            "--verify" => index += 1,
            value if value.starts_with("-psn_") => index += 1,
            _ => return Err("Unknown Reality Local argument".into()),
        }
    }
    if operation == Some("--restore") && !confirmed {
        return Err("Restore requires --confirm-restore".into());
    }
    if confirmed && operation != Some("--restore") {
        return Err("--confirm-restore requires --restore".into());
    }
    let erasure_confirmed = forwarded.iter().any(|value| value == "--confirm-erasure");
    if operation == Some("--erase") && !erasure_confirmed {
        return Err("Erasure requires --confirm-erasure".into());
    }
    if erasure_confirmed && operation != Some("--erase") {
        return Err("--confirm-erasure requires --erase".into());
    }
    Ok(forwarded)
}

/// A failed start must end with a readable reason, never a crash report.
fn start(app: &mut tauri::App) -> Result<(), Setup> {
    let resources = app.path().resource_dir()?;
    let onboarding = resources.join("probe/local-runtime.py").exists();
    // A persistent installation must not present itself as a disposable test.
    let disposable = resources.join("probe/disposable").exists();
    let unsigned_tester_beta = resources.join("probe/unsigned-tester-beta").exists();
    let script = if onboarding {
        "probe/local-runtime.py"
    } else {
        "probe/native-probe.py"
    };
    let native_arguments: Vec<String> = std::env::args().skip(1).collect();
    let maintenance = maintenance_arguments(&native_arguments)?;
    if !onboarding && !maintenance.is_empty() {
        return Err("Maintenance requires the installed Reality Local product".into());
    }
    let mut command = Command::new(resources.join("runtime/python/bin/python3.12"));
    command
        .arg("-I")
        // Never write bytecode: the bundle is signed and must stay unchanged.
        .arg("-B")
        .arg(resources.join(script))
        .env_clear()
        .env("PATH", "/usr/bin:/bin")
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    command.args(&maintenance);
    let mut child = command.spawn()?;
    let stdout = child.stdout.take().ok_or("Missing private control pipe")?;
    let mut reader = BufReader::new(stdout);
    if onboarding && !disposable {
        let mut message = String::new();
        reader.read_line(&mut message)?;
        let bundle_identifier = app.config().identifier.clone();
        let stdin = child
            .stdin
            .as_mut()
            .ok_or("Missing private Keychain pipe")?;
        let envelope: serde_json::Value = serde_json::from_str(&message)?;
        if envelope["kind"] == "keychain_request" {
            let request: KeychainRequest = serde_json::from_value(envelope)?;
            if request.kind != "keychain_request" {
                return Err("Invalid native Keychain request".into());
            }
            let secrets = keychain::installation_secrets(
                &bundle_identifier,
                &request.installation_id,
                request.legacy_database_password.as_deref(),
            )?;
            serde_json::to_writer(
                &mut *stdin,
                &KeychainResponse {
                    kind: "keychain_response",
                    installation_id: request.installation_id,
                    database_password: secrets.database_password,
                    vault_master_key: secrets.vault_master_key,
                },
            )?;
        } else if envelope["kind"] == "keychain_erasure_request" {
            let request: KeychainErasureRequest = serde_json::from_value(envelope)?;
            if request.kind != "keychain_erasure_request"
                || !["delete", "inspect"].contains(&request.operation.as_str())
            {
                return Err("Invalid native Keychain erasure request".into());
            }
            if request.operation == "delete" {
                let _ = keychain::delete_installation_secrets(
                    &bundle_identifier,
                    &request.installation_id,
                );
            }
            let state = match keychain::installation_secret_state(
                &bundle_identifier,
                &request.installation_id,
            )? {
                keychain::InstallationSecretState::Present => "present",
                keychain::InstallationSecretState::Missing => "missing",
                keychain::InstallationSecretState::Partial => "partial",
            };
            serde_json::to_writer(
                &mut *stdin,
                &KeychainErasureResponse {
                    kind: "keychain_erasure_response",
                    installation_id: request.installation_id,
                    state,
                },
            )?;
        } else if envelope["kind"] == "beta_custody_request" && unsigned_tester_beta {
            let request: BetaCustodyRequest = serde_json::from_value(envelope)?;
            if request.kind != "beta_custody_request" {
                return Err("Invalid native beta custody request".into());
            }
            serde_json::to_writer(
                &mut *stdin,
                &BetaCustodyResponse {
                    kind: "beta_custody_response",
                    installation_id: request.installation_id,
                },
            )?;
        } else if envelope["kind"] == "keychain_migration_request" && !unsigned_tester_beta {
            let request: KeychainMigrationRequest = serde_json::from_value(envelope)?;
            if request.kind != "keychain_migration_request" {
                return Err("Invalid native Keychain migration request".into());
            }
            keychain::migrate_installation_secrets(
                &bundle_identifier,
                &request.installation_id,
                &request.database_password,
                &request.vault_master_key,
            )?;
            serde_json::to_writer(
                &mut *stdin,
                &KeychainMigrationResponse {
                    kind: "keychain_migration_response",
                    installation_id: request.installation_id,
                    exact: true,
                },
            )?;
        } else {
            return Err("Invalid native Keychain request".into());
        }
        stdin.write_all(b"\n")?;
        stdin.flush()?;
    }
    if !maintenance.is_empty() {
        let mut message = String::new();
        reader.read_line(&mut message)?;
        let result: serde_json::Value = serde_json::from_str(&message)?;
        if result["kind"].as_str() != Some("operation_result") {
            return Err("Native maintenance operation failed".into());
        }
        println!("{}", serde_json::to_string(&result)?);
        let status = child.wait()?;
        std::process::exit(if status.success() { 0 } else { 1 });
    }
    app.manage(Probe(Mutex::new(child)));
    let handle = app.handle().clone();
    let verify = std::env::args().any(|argument| argument == "--verify");
    let (sender, receiver) = std::sync::mpsc::sync_channel(1);
    std::thread::spawn(move || {
        let mut message = String::new();
        if reader.read_line(&mut message).is_ok() {
            let _ = sender.send(message);
        }
        for line in reader.lines().map_while(Result::ok) {
            if let Ok(proof) = serde_json::from_str::<serde_json::Value>(&line) {
                eprintln!(
                    "Native cookie proof: cookie_hidden={}, native_command_denied={}",
                    proof["cookie_hidden"].as_bool().unwrap_or(false),
                    proof["native_command_denied"].as_bool().unwrap_or(false)
                );
                if verify {
                    let success = proof["cookie_hidden"].as_bool() == Some(true)
                        && proof["native_command_denied"].as_bool() == Some(true);
                    handle.exit(if success { 0 } else { 2 });
                }
            }
        }
    });
    let message = receiver.recv_timeout(std::time::Duration::from_secs(180))?;
    let endpoint: Endpoint = serde_json::from_str(&message)?;
    let url: tauri::Url = endpoint.origin.parse()?;
    if url.scheme() != "http" || url.host_str() != Some("127.0.0.1") || url.port().is_none() {
        return Err("Invalid private endpoint".into());
    }
    let mut builder = tauri::WebviewWindowBuilder::new(
        app,
        "preview",
        tauri::WebviewUrl::External("about:blank".parse()?),
    )
    .title(match (onboarding, disposable) {
        (true, true) => "Reality Local — Test Installation",
        (true, false) => "Reality Local",
        _ => "Reality Local Preview",
    })
    .inner_size(1440.0, 960.0)
    .prevent_overflow()
    .center()
    .visible(false)
    .incognito(true)
    .on_navigation({
        let origin = endpoint.origin.clone();
        move |url| url.as_str() == "about:blank" || url.origin().ascii_serialization() == origin
    });
    if verify && onboarding {
        builder = builder.initialization_script(r#"
                    document.addEventListener('DOMContentLoaded', async()=>{
                      if(location.pathname !== '/app') return;
                      let denied=false; try {await window.__TAURI_INTERNALS__.invoke('plugin:app|version');} catch(e) {denied=/not allowed|denied|not permitted/i.test(String(e));}
                      const authenticated=(await fetch('/api/auth/me')).ok;
                      await fetch('/api/desktop/proof',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cookie_hidden:authenticated&&!document.cookie.includes('reality_session'),native_command_denied:denied})});
                    });
                "#);
    }
    let window = builder.build()?;
    if !["reality_native_probe", "reality_session"].contains(&endpoint.cookie_name.as_str())
        || !["/", "/app"].contains(&endpoint.path.as_str())
    {
        return Err("Invalid native session target".into());
    }
    let cookie = tauri::webview::Cookie::build((endpoint.cookie_name, endpoint.token))
        .domain("127.0.0.1")
        .path("/")
        .http_only(true)
        .same_site(tauri::webview::cookie::SameSite::Strict)
        .build();
    window.set_cookie(cookie)?;
    window.navigate(url.join(&endpoint.path)?)?;
    window.show()?;
    Ok(())
}

#[cfg(test)]
mod maintenance_tests {
    use super::maintenance_arguments;

    fn values(items: &[&str]) -> Vec<String> {
        items.iter().map(|item| (*item).to_owned()).collect()
    }

    #[test]
    fn restore_requires_confirmation() {
        assert!(maintenance_arguments(&values(&["--restore", "/tmp/backup"])).is_err());
        assert!(
            maintenance_arguments(&values(&["--restore", "/tmp/backup", "--confirm-restore"]))
                .is_ok()
        );
    }

    #[test]
    fn backup_and_restore_cannot_be_combined() {
        assert!(maintenance_arguments(&values(&[
            "--backup",
            "/tmp/one",
            "--restore",
            "/tmp/two",
            "--confirm-restore"
        ]))
        .is_err());
    }

    #[test]
    fn erasure_requires_exact_confirmation() {
        assert!(maintenance_arguments(&values(&["--erase"])).is_err());
        assert!(maintenance_arguments(&values(&["--erase", "--confirm-erasure"])).is_ok());
        assert!(maintenance_arguments(&values(&["--confirm-erasure"])).is_err());
    }
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            if let Err(error) = start(app) {
                eprintln!("Reality Local could not start: {error}");
                std::process::exit(1);
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Unable to start Reality Local Preview")
        .run(|app, event| {
            if matches!(event, tauri::RunEvent::Exit) {
                if let Some(probe) = app.try_state::<Probe>() {
                    if let Ok(mut child) = probe.0.lock() {
                        stop_child(&mut child);
                    }
                }
            }
        });
}
