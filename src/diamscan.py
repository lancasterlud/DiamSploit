#!/usr/bin/env python

import ipaddress
import socket, errno
import diameter
import diameter.common_messages as cm

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

init()

def pretty_errno(code: int):
    name = errno.errorcode.get(code, "UNKOWN")
    message = os.strerror(code)
    return f"{name} {code}: {message}"

def send_diameter_message(s):
    # DIAMETER message (CER)
    cer = cm.CapabilitiesExchangeRequest(diameter.VERSION_ONE)
    cer.origin_host("mme01".encode("ascii"))
    cer.origin_realm("epc.mnc01.mcc001.3gppnetwork.org".encode("ascii"))
    cer.vendor_id(0)
    cer.product_name("DiamSploit".encode("ascii"))
    cer.build()
    s.send(cer.get_msg())
    # DIAMETER response (CEA)
    cea = diameter.DiameterResponse(s.recv(4096))
    cea.process()
    return cea.avps[264][0].data.decode("ascii")  # Origin-Host AVP

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
        if conn == 0:
            origin_host = send_diameter_message(s)
    except OSError as e:
        print(Fore.RED + f"[!] Error connecting to {ip} - {e}" + Style.RESET_ALL)
    finally:
        s.close()

    # Evalutation
    if conn == 0:
        print(Fore.GREEN + f"[+] DIAMETER FOUND on {ip}" + Style.RESET_ALL)
        return (ip, "open", origin_host)
    elif conn == errno.ECONNREFUSED:
        print(Fore.RED + f"[-] {ip} closed" + Style.RESET_ALL)
        return (ip, "closed")
    elif conn in (errno.ETIMEDOUT, errno.EAGAIN, errno.EWOULDBLOCK, errno.EHOSTUNREACH):
        return (ip, "unreachable")
    else:
        print(
            Fore.MAGENTA
            + f"[?] Status of {ip} is unknown (error code: {pretty_errno(conn)})"
            + Style.RESET_ALL
        )
        return (ip, "unknown")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diameter protocol scanner")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--network", 
        type=str, 
        help="Network range in CIDR notation (e.g., 192.168.1.0/24)"
    )
    target_group.add_argument(
        "--host", 
        type=str, 
        help="Single host IP address to scan (e.g., 192.168.1.1)"
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
    print(f"    Host:     {args.host}") if args.host else print(f"    Network:  {args.network}")
    print(f"    Port:     {args.port}")
    print(f"    Timeout:  {args.timeout} seconds")
    print(f"    Protocol: {args.protocol.upper()}\n")
    print(Fore.YELLOW + "[*] Starting DIAMETER scan..." + Style.RESET_ALL)

    # Single host scan
    if args.host:
        result = scan_diameter(args.host, args.port, args.timeout, args.protocol)
        if result[1] == "open":
            print(Fore.GREEN + f"[+] DIAMETER service discovered on {args.host} with Origin-Host: {result[2]}" + Style.RESET_ALL)
        exit()

    # Multi-thread scan
    net = ipaddress.ip_network(args.network)
    discovered = []
    results = {
        "open": 0,
        "closed": 0,
        "unreachable": 0,
        "unknown": 0
    }
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
        print(Fore.GREEN + f"[+] DIAMETER service discovered on {host[0]} with Origin-Host: {host[2]}" + Style.RESET_ALL)
