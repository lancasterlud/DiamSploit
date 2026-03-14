#!/usr/bin/env python3

import diameter.base_diameter as diameter
import socket
import struct

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

    # Build requests
    print("[*] Initialize Diameter stack ...")
    cer = diameter.DiameterRequest(1, diameter.CER_COMMAND_CODE)
    cer.add_avp(264, 0x40, b"diamsploit-client")
    cer.add_avp(296, 0x40, b"localdomain")
    cer.add_avp(266, 0x40, struct.pack("!I", 0))
    cer.add_avp(269, 0x00, b"diamsploit")
    cer.build()
    
    dwr = diameter.DiameterRequest(1, diameter.DWR_COMMAND_CODE)
    dwr.add_avp(264, 0x40, b"diamsploit-client")
    dwr.add_avp(296, 0x40, b"localdomain")
    dwr.build()

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
        
    s.close()
