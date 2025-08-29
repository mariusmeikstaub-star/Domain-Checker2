import argparse
import sys
from typing import List, Optional

import requests


def check_domain(domain: str, timeout: float = 10.0) -> Optional[bool]:
    """Check via RDAP whether *domain* is registered.

    Returns ``True`` if the domain is registered, ``False`` if the domain
    appears to be available and ``None`` if the status could not be
    determined due to a network issue or unexpected response.
    """
    url = f"https://rdap.org/domain/{domain}"
    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException:
        return None

    if response.status_code == 404:
        return False
    if 200 <= response.status_code < 300:
        return True
    return None


def read_domains_from_file(path: str) -> List[str]:
    """Return a list of domains loaded from *path*.

    Each non-empty line in the file is treated as a domain name. Lines
    starting with a ``#`` are ignored so that the file can contain
    comments.
    """
    domains: List[str] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            domains.append(line)
    return domains


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check domain registration status using RDAP")
    parser.add_argument("domains", nargs="*", help="Domain names to check")
    parser.add_argument("-f", "--file", dest="file", help="Path to a file with one domain per line")
    args = parser.parse_args(argv)

    domains: List[str] = []
    domains.extend(args.domains)

    if args.file:
        try:
            domains.extend(read_domains_from_file(args.file))
        except OSError as exc:
            print(f"Could not read {args.file}: {exc}", file=sys.stderr)
            return 1

    if not domains:
        parser.print_usage()
        return 1

    for domain in domains:
        status = check_domain(domain)
        if status is True:
            print(f"{domain}: registered")
        elif status is False:
            print(f"{domain}: available")
        else:
            print(f"{domain}: unknown")
    return 0


if __name__ == "__main__":  # pragma: no cover - direct execution only
    raise SystemExit(main())
