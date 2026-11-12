#!/usr/bin/env python

import ipaddress
import socket, errno
import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

init()

def pretty_errno(code: int):
    name = errno.errorcode.get(code, "UNKOWN")
    message = os.strerror(code)
    return f"{name} {code}: {message}"

def scan_diameter(ip, port, timeout, protocol="sctp"):
    # Connection
    s = socket.socket(
        socket.AF_INET, 
        socket.SOCK_STREAM, 
        socket.IPPROTO_SCTP if protocol == "sctp" else socket.IPPROTO_TCP
    )
    try:
        s.settimeout(timeout)
        conn = s.connect_ex((str(ip), port))
    except OSError as e:
        print(Fore.RED + f"[!] Error connecting to {ip} - {e}" + Style.RESET_ALL)
    finally:
        s.close()

    # Evalutation
    if conn == 0:
        print(Fore.GREEN + f"[+] DIAMETER FOUND on {ip}" + Style.RESET_ALL)
        status = "open"
    elif conn == errno.ECONNREFUSED:
        print(Fore.RED + f"[-] {ip} closed" + Style.RESET_ALL)
        status = "closed"
    elif conn in (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK, errno.EHOSTUNREACH):
        status = "unreachable"
    else:
        print(
            Fore.MAGENTA
            + f"[?] Status of {ip} is unknown (error code: {pretty_errno(conn)})"
            + Style.RESET_ALL
        )
        status = "unknown"
    return (ip, status)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diameter protocol scanner")
    parser.add_argument(
        "--network", 
        type=str, 
        required=True, 
        help="Network range in CIDR notation (e.g., 192.168.1.0/24)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=3868, 
        help="Port number to scan (default: 3868)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=5, 
        help="Timeout in seconds for socket connection (default: 5)"
    )
    parser.add_argument(
        "--protocol", 
        type=str, 
        default="sctp",
        choices=["tcp", "sctp"],
        help="Protocol to use (default: sctp)"
    )
    args = parser.parse_args()

    print(Fore.CYAN + "\n[*] Scan parameters:" + Style.RESET_ALL)
    print(f"    Network:  {args.network}")
    print(f"    Port:     {args.port}")
    print(f"    Timeout:  {args.timeout} seconds")
    print(f"    Protocol: {args.protocol.upper()}\n")
    print(Fore.YELLOW + "[*] Starting DIAMETER scan..." + Style.RESET_ALL)
    net = ipaddress.ip_network(args.network)
    discovered = []
    results = {
        "open": 0,
        "closed": 0,
        "unreachable": 0,
        "unknown": 0
    }

    # Multi-thread scan
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_diameter, ip, args.port, args.timeout, args.protocol) for ip in net.hosts()]
        for future in as_completed(futures):
            future_result = future.result()
            if future_result[1] == "open":
                discovered.append(future_result[0])
            results[future_result[1]] += 1
    
    print(Fore.CYAN + "\n[*] Scan completed:" + Style.RESET_ALL)
    print(f"    Open: {results['open']}")
    print(f"    Closed: {results['closed']}")
    print(f"    Unreachable: {results['unreachable']}")
    print(f"    Unknown: {results['unknown']}\n")

    for host in discovered:
        print(Fore.GREEN + f"[+] DIAMETER service discovered on {host[0]}" + Style.RESET_ALL)
