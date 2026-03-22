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

if __name__ == "__main__":
    
    title = figlet_format("DiamSploit")
    print(Fore.BLUE + title + Style.RESET_ALL)

    # Get params
    if ENV_FILE.exists():
        print("[*] Found .env file")
        load_dotenv(ENV_FILE)
        host = os.getenv("HOST")
        port = int(os.getenv("PORT"))
        buffer = int(os.getenv("BUFFER"))
    else:
        host = input("Enter peer IP address: ")
        port = int(input("Enter peer port (default 3868): "))
        buffer = 4096

    origin_host = input("Enter your origin host: ")
    origin_realm = input("Enter your origin realm: ")
    origin_host = origin_host.encode("ascii")
    origin_realm = origin_realm.encode("ascii")

    # Build requests
    print("[*] Initialize Diameter stack ...")
    cer = cm.CapabilitiesExchangeRequest(diameter.VERSION_ONE)
    cer.origin_host(origin_host)
    cer.origin_realm(origin_realm)
    cer.vendor_id(0)
    cer.product_name(b"DiamSploit")
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
    
    print("[*] Sending Capabilities-Exchange-Request (CER) ...")
    s.send(cer.get_msg())
    cea = s.recv(buffer)
    print(Fore.GREEN + "[+] Response (CEA): " + Style.RESET_ALL, " ".join(f"{b:02X}" for b in cea))
    
    print("[*] Sending Device-Watchdog-Request (DWR) ...")
    s.send(dwr.get_msg())
    dwa = s.recv(buffer)
    print(Fore.GREEN + "[+] Response (DWA): " + Style.RESET_ALL, " ".join(f"{b:02X}" for b in dwa))
        
    print("[*] Sending Disconnect-Peer-Request (DPR) ...")
    s.send(dpr.get_msg())
    dpa = s.recv(buffer)
    print(Fore.GREEN + "[+] Response (DPA): " + Style.RESET_ALL, " ".join(f"{b:02X}" for b in dpa))

    s.close()
