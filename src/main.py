#!/usr/bin/env python3

from diameter.diameter_common_messages import *
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
    cer = DiameterRequest(VERSION_ONE, CER_COMMAND_CODE)
    cer.add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    cer.add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    cer.add_avp(AVP_VENDOR_ID, 0x40, 0)
    cer.add_avp(AVP_PRODUCT_NAME, 0x00, b"diamsploit")
    cer.build()
    
    dwr = DiameterRequest(VERSION_ONE, DWR_COMMAND_CODE)
    dwr.add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    dwr.add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    dwr.build()

    dpr = DiameterRequest(VERSION_ONE, DPR_COMMAND_CODE)
    dpr.add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    dpr.add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    dpr.add_avp(AVP_DISCONNECT_CAUSE, 0x40, DISCONNECT_CAUSE_DO_NOT_WANT_TO_TALK_TO_YOU)
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
