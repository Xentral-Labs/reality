//! Desktop socket ownership proof. No fixed ports and no probe/close/rebind window.
//!
//! This is exercised by the standalone spike; it is not wired into the product yet.
use std::collections::BTreeMap;
use std::io;
use std::net::{Ipv4Addr, SocketAddr, TcpListener};

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum Role {
    Api,
    Scheduler,
    Worker,
}

impl Role {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "api" => Some(Self::Api),
            "scheduler" => Some(Self::Scheduler),
            "worker" => Some(Self::Worker),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::Api => "api",
            Self::Scheduler => "scheduler",
            Self::Worker => "worker",
        }
    }
}

/// The listener stays owned until serving completes; its port is never a reservation hint.
pub struct BoundEndpoint {
    listener: TcpListener,
    pub role: Role,
    pub generation: u64,
}

impl BoundEndpoint {
    pub fn bind(role: Role, generation: u64) -> io::Result<Self> {
        Self::bind_with(role, generation, || {
            TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
        })
    }

    fn bind_with(
        role: Role,
        generation: u64,
        mut bind: impl FnMut() -> io::Result<TcpListener>,
    ) -> io::Result<Self> {
        for attempt in 0..3 {
            match bind() {
                Ok(listener) => {
                    let address = listener.local_addr()?;
                    if address.ip() != Ipv4Addr::LOCALHOST || address.port() == 0 {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidInput,
                            "Desktop listeners must bind IPv4 loopback",
                        ));
                    }
                    return Ok(Self {
                        listener,
                        role,
                        generation,
                    });
                }
                Err(error) if error.kind() == io::ErrorKind::AddrInUse && attempt < 2 => {}
                Err(error) => return Err(error),
            }
        }
        unreachable!("Every final attempt returns its outcome")
    }

    pub fn address(&self) -> io::Result<SocketAddr> {
        self.listener.local_addr()
    }

    pub fn origin(&self) -> io::Result<String> {
        Ok(format!("http://{}", self.address()?))
    }

    pub fn into_listener(self) -> TcpListener {
        self.listener
    }
}

/// A consumer must explicitly retire the old endpoint before accepting a new role instance.
pub struct EndpointRegistry {
    generations: BTreeMap<Role, u64>,
    addresses: BTreeMap<Role, SocketAddr>,
}

impl Default for EndpointRegistry {
    fn default() -> Self {
        Self::new()
    }
}

impl EndpointRegistry {
    pub fn new() -> Self {
        Self {
            generations: BTreeMap::new(),
            addresses: BTreeMap::new(),
        }
    }

    pub fn expect(&mut self, role: Role, generation: u64) -> bool {
        if self
            .generations
            .get(&role)
            .is_some_and(|old| *old >= generation)
        {
            return false;
        }
        self.generations.insert(role, generation);
        self.addresses.remove(&role);
        true
    }

    pub fn report(&mut self, role: Role, generation: u64, address: SocketAddr) -> bool {
        if self.generations.get(&role) != Some(&generation)
            || address.ip() != Ipv4Addr::LOCALHOST
            || address.port() == 0
        {
            return false;
        }
        // Duplicate identical delivery is idempotent; replacement needs a new generation.
        if let Some(current) = self.addresses.get(&role) {
            return *current == address;
        }
        self.addresses.insert(role, address);
        true
    }

    pub fn address(&self, role: Role) -> Option<SocketAddr> {
        self.addresses.get(&role).copied()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn address_exhaustion_is_bounded() {
        let mut calls = 0;
        let result = BoundEndpoint::bind_with(Role::Api, 1, || {
            calls += 1;
            Err(io::Error::from(io::ErrorKind::AddrInUse))
        });
        assert!(result.is_err());
        assert_eq!(calls, 3);
    }

    #[test]
    fn resource_exhaustion_does_not_spin() {
        let mut calls = 0;
        let result = BoundEndpoint::bind_with(Role::Api, 1, || {
            calls += 1;
            Err(io::Error::from_raw_os_error(24)) // EMFILE on macOS/Linux.
        });
        assert_eq!(result.err().unwrap().raw_os_error(), Some(24));
        assert_eq!(calls, 1);
    }

    #[test]
    fn transient_allocation_failure_keeps_the_successful_socket() {
        let mut calls = 0;
        let endpoint = BoundEndpoint::bind_with(Role::Api, 1, || {
            calls += 1;
            if calls == 1 {
                return Err(io::Error::from(io::ErrorKind::AddrInUse));
            }
            TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
        })
        .unwrap();
        assert_eq!(calls, 2);
        assert!(TcpListener::bind(endpoint.address().unwrap()).is_err());
    }

    #[test]
    fn stale_reports_cannot_restore_a_previous_endpoint() {
        let mut registry = EndpointRegistry::new();
        let old = BoundEndpoint::bind(Role::Api, 1).unwrap();
        let new = BoundEndpoint::bind(Role::Api, 2).unwrap();
        assert!(!registry.report(Role::Api, 1, old.address().unwrap()));
        assert!(registry.expect(Role::Api, 1));
        assert!(registry.report(Role::Api, 1, old.address().unwrap()));
        assert!(registry.expect(Role::Api, 2));
        assert_eq!(registry.address(Role::Api), None);
        assert!(!registry.report(Role::Api, 1, old.address().unwrap()));
        assert!(!registry.expect(Role::Api, 1));
        assert!(registry.report(Role::Api, 2, new.address().unwrap()));
        assert!(registry.report(Role::Api, 2, new.address().unwrap()));
        assert!(!registry.report(Role::Api, 2, old.address().unwrap()));
        assert_eq!(registry.address(Role::Api), Some(new.address().unwrap()));
    }

    #[test]
    fn reports_are_role_scoped_and_loopback_only() {
        let mut registry = EndpointRegistry::new();
        registry.expect(Role::Api, 1);
        for address in ["0.0.0.0:9000", "192.0.2.1:9000", "127.0.0.1:0"] {
            assert!(!registry.report(Role::Api, 1, address.parse().unwrap()));
        }
        assert!(!registry.report(Role::Worker, 1, "127.0.0.1:9000".parse().unwrap()));
    }

    #[test]
    fn dropping_partial_startup_releases_owned_listeners() {
        let first = BoundEndpoint::bind(Role::Api, 1).unwrap();
        let address = first.address().unwrap();
        let result =
            BoundEndpoint::bind_with(Role::Worker, 1, || Err(io::Error::from_raw_os_error(24)));
        assert!(result.is_err());
        drop(first);
        assert!(TcpListener::bind(address).is_ok());
    }
}
