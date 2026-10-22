import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal"}
_NAT64 = ipaddress.ip_network("64:ff9b::/96")


class UnsafeURLError(ValueError):
    """The URL is malformed or points at a non-public address."""


def _resolve(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return list({info[4][0] for info in infos})


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address.split("%")[0])
    if ip.version == 6:
        if ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        elif ip in _NAT64:
            ip = ipaddress.ip_address(int(ip) & 0xFFFFFFFF)
    # is_global is False for loopback, private, link-local (incl. 169.254.169.254),
    # shared 100.64/10, reserved, multicast and unspecified addresses.
    return ip.is_global


def validate_url(url: str) -> None:
    """Raise UnsafeURLError unless url is http(s) and only resolves to public addresses.
    Hosts that do not resolve at all are allowed: there is nothing to connect to,
    and the check will simply record a connection error.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        raise UnsafeURLError("Enter a full http:// or https:// URL.")

    # Scheme must be http or https
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("Enter a full http:// or https:// URL.")
    
    # Host must be present
    if not parsed.hostname:
        raise UnsafeURLError("Enter a full http:// or https:// URL.")

    # Credentials not allowed
    if parsed.username or parsed.password:
        raise UnsafeURLError("URLs with a username or password are not allowed.")

    host = parsed.hostname
    port = parsed.port

    blocked = UnsafeURLError("That address is not allowed (private or internal network).")
    name = host.lower().rstrip(".")
    if name in BLOCKED_HOSTNAMES or name.endswith(".localhost"):
        raise blocked

    try:
        addresses = [str(ipaddress.ip_address(name))]
    except ValueError:
        try:
            addresses = _resolve(name, port or (443 if parsed.scheme == "https" else 80))
        except socket.gaierror:
            return
    if not all(_is_public(a) for a in addresses):
        raise blocked
