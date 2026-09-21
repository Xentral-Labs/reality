use std::io::{BufRead, BufReader};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::Manager;

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

type Setup = Box<dyn std::error::Error>;

/// A failed start must end with a readable reason, never a crash report.
fn start(app: &mut tauri::App) -> Result<(), Setup> {
    {
            let resources = app.path().resource_dir()?;
            let onboarding = resources.join("probe/local-runtime.py").exists();
            // A persistent installation must not present itself as a disposable test.
            let disposable = resources.join("probe/disposable").exists();
            let script = if onboarding { "probe/local-runtime.py" } else { "probe/native-probe.py" };
            let mut child = Command::new(resources.join("runtime/python/bin/python3.12"))
                .arg("-I")
                .arg(resources.join(script))
                .env_clear()
                .env("PATH", "/usr/bin:/bin")
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .spawn()?;
            let stdout = child.stdout.take().ok_or("Missing private control pipe")?;
            app.manage(Probe(Mutex::new(child)));
            let handle = app.handle().clone();
            let verify = std::env::args().any(|argument| argument == "--verify");
            let (sender, receiver) = std::sync::mpsc::sync_channel(1);
            std::thread::spawn(move || {
                let mut reader = BufReader::new(stdout);
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
            if url.scheme() != "http" || url.host_str() != Some("127.0.0.1") || url.port().is_none()
            {
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
                move |url| {
                    url.as_str() == "about:blank" || url.origin().ascii_serialization() == origin
                }
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
            if !["reality_native_probe", "reality_session"].contains(&endpoint.cookie_name.as_str()) || !["/", "/app"].contains(&endpoint.path.as_str()) { return Err("Invalid native session target".into()); }
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
