#!/usr/bin/env python

import diameter
import diameter.common_messages as cm
import socket

from colorama import Fore, Style
from pyfiglet import figlet_format
from dotenv import load_dotenv
from pathlib import Path
import os

# .env file path
ENV_FILE = Path(__file__).parent.parent / ".env"

def send_capabilities_exchange(cer, s, buffer):
    print(Fore.YELLOW + "[*] Sending Capabilities-Exchange Request (CER) ..." + Style.RESET_ALL)
    s.send(cer.get_msg())
    cea = diameter.DiameterResponse(s.recv(buffer))
    cea.process()
    if cea.success():
        print(Fore.GREEN + "[+] DIAMETER_SUCCESS (CEA)" + Style.RESET_ALL)
        print("[+] Origin-Host: " + Fore.RED + cea.avps[diameter.AVP_ORIGIN_HOST][0].data.decode("ascii") + Style.RESET_ALL)
        print("[+] Origin-Realm: " + Fore.RED + cea.avps[diameter.AVP_ORIGIN_REALM][0].data.decode("ascii") + Style.RESET_ALL)
    else:
        print(Fore.RED + "[+] DIAMETER_FAILURE (CEA)" + Style.RESET_ALL)

def send_device_watchdog(dwr, s, buffer):
    print(Fore.YELLOW + "[*] Sending Device-Watchdog Request (DWR) ..." + Style.RESET_ALL)
    s.send(dwr.get_msg())
    dwa = diameter.DiameterResponse(s.recv(buffer))
    dwa.process()
    if dwa.success():
        print(Fore.GREEN + "[+] DIAMETER_SUCCESS (DWA)" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[+] DIAMETER_FAILURE (DWA)" + Style.RESET_ALL)

def send_disconnect_peer(dpr, s, buffer):
    print(Fore.YELLOW + "[*] Sending Disconnect-Peer Request (DPR) ..." + Style.RESET_ALL)
    s.send(dpr.get_msg())
    dpa = diameter.DiameterResponse(s.recv(buffer))
    dpa.process()
    if dpa.success():
        print(Fore.GREEN + "[+] DIAMETER_SUCCESS (DPA)" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[+] DIAMETER_FAILURE (DPA)" + Style.RESET_ALL)

if __name__ == "__main__":
    
    title = figlet_format("DiamSploit")
    print(Fore.RED + title + Style.RESET_ALL)

    # Get params
    if ENV_FILE.exists():
        print(Fore.GREEN + "[+] Found .env file\n" + Style.RESET_ALL)
        load_dotenv(ENV_FILE)
        host = os.getenv("HOST")
        port = int(os.getenv("PORT"))
        origin_host = os.getenv("ORIGIN_HOST")
        origin_realm = os.getenv("ORIGIN_REALM")
        product_name = os.getenv("PRODUCT_NAME")
        buffer = int(os.getenv("BUFFER"))
    else:
        host = input("Enter peer IP address > ")
        port = int(input("Enter peer port (default 3868) > "))
        origin_host = input("Enter your origin host > ")
        origin_realm = input("Enter your origin realm > ")
        product_name = input("Enter your product name > ")
        buffer = 4096

    origin_host = origin_host.encode("ascii")
    origin_realm = origin_realm.encode("ascii")
    product_name = product_name.encode("ascii")

    # Build requests
    print("\n[*] Initialize DIAMETER stack ...")
    cer = cm.CapabilitiesExchangeRequest(diameter.VERSION_ONE)
    cer.origin_host(origin_host)
    cer.origin_realm(origin_realm)
    cer.vendor_id(0)
    cer.product_name(product_name)
    cer.build()
    
    dwr = cm.DeviceWatchdogRequest(diameter.VERSION_ONE)
    dwr.origin_host(origin_host)
    dwr.origin_realm(origin_realm)
    dwr.build()

    dpr = cm.DisconnectPeerRequest(diameter.VERSION_ONE)
    dpr.origin_host(origin_host)
    dpr.origin_realm(origin_realm)
    dpr.disconnect_cause(cm.DISCONNECT_CAUSE_DO_NOT_WANT_TO_TALK_TO_YOU)
    dpr.build()

    # Server connection
    print("[*] Connecting to server ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    print(Fore.GREEN + "[+] Connection established\n" + Style.RESET_ALL)

    command = input("(" + Fore.RED + host + Style.RESET_ALL + ") > ")
    while command != "dpr":
        if command == "cer":
            send_capabilities_exchange(cer, s, buffer)
        elif command == "dwr":
            send_device_watchdog(dwr, s, buffer)
        command = input("(" + Fore.RED + host + Style.RESET_ALL + ") > ")

    send_disconnect_peer(dpr, s, buffer)
    s.close()
