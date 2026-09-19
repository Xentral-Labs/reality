//! Bounded health-only socket probe. This executable has no application or data access.
use reality_desktop_port_probe::{BoundEndpoint, Role};
use std::io::{self, Read, Write};
use std::time::Duration;

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let role = args
        .next()
        .and_then(|arg| Role::parse(&arg))
        .ok_or("Invalid role")?;
    let generation: u64 = args.next().ok_or("Missing generation")?.parse()?;
    if args.next().is_some() {
        return Err("Unexpected arguments".into());
    }
    let endpoint = BoundEndpoint::bind(role, generation)?;
    let address = endpoint.address()?;
    println!(
        "{{\"role\":\"{}\",\"generation\":{},\"origin\":\"{}\"}}",
        role.as_str(),
        generation,
        endpoint.origin()?
    );
    io::stdout().flush()?;
    // Serve on the SAME socket that produced the announced endpoint.
    let listener = endpoint.into_listener();
    for incoming in listener.incoming() {
        let mut stream = incoming?;
        stream.set_read_timeout(Some(Duration::from_secs(1)))?;
        stream.set_write_timeout(Some(Duration::from_secs(1)))?;
        let mut request = Vec::new();
        let mut chunk = [0; 512];
        while !request.ends_with(b"\r\n\r\n") && request.len() < 4096 {
            match stream.read(&mut chunk) {
                Ok(0) | Err(_) => break,
                Ok(count) => request.extend_from_slice(&chunk[..count]),
            }
        }
        let text = String::from_utf8_lossy(&request);
        let expected_host = format!("host: {}", address);
        let correct_host = text
            .lines()
            .any(|line| line.to_ascii_lowercase() == expected_host);
        let (status, body) = if correct_host && text.starts_with("GET /healthz HTTP/1.1\r\n") {
            (
                "200 OK",
                format!(
                    "{{\"role\":\"{}\",\"generation\":{}}}",
                    role.as_str(),
                    generation
                ),
            )
        } else {
            ("400 Bad Request", "{}".to_owned())
        };
        let response = format!(
            "HTTP/1.1 {status}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
            body.len()
        );
        // A disconnected probe client does not terminate the role.
        let _ = stream.write_all(response.as_bytes());
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("Desktop port probe failed: {error}");
        std::process::exit(1);
    }
}
