from dataclasses import dataclass
from typing import ClassVar
import struct
import random

# Version
VERSION_ONE = 1

# Command codes
CER_COMMAND_CODE = 257
DWR_COMMAND_CODE = 280
DPR_COMMAND_CODE = 282

# Application ID
DIAMETER_COMMON_MESSAGES_APPLICATION_ID = 0

# AVP codes
AVP_ORIGIN_HOST = 264
AVP_ORIGIN_REALM = 296
AVP_VENDOR_ID = 266
AVP_PRODUCT_NAME = 269
AVP_DISCONNECT_CAUSE = 273

# Disconnect-Cause codes
DISCONNECT_CAUSE_REBOOTING = 0
DISCONNECT_CAUSE_BUSY = 1
DISCONNECT_CAUSE_DO_NOT_WANT_TO_TALK_TO_YOU = 2

@dataclass
class DiameterHeader:
    version: int
    avps_length: int
    flags: int
    command_code: int
    application_id: int

    HEADER_LENGTH: ClassVar[int] = 20
        
    def to_bytes(self):
        header = struct.pack("!B", self.version)
        header += struct.pack("!I", self.HEADER_LENGTH + self.avps_length)[1:]
        header += struct.pack("!B", self.flags)
        header += struct.pack("!I", self.command_code)[1:]
        header += struct.pack("!I", self.application_id)
        header += struct.pack("!I", random.randint(1, 0xffffffff))
        header += struct.pack("!I", random.randint(1, 0xffffffff))
        return header

@dataclass
class DiameterAVP:
    code: int
    flags: int
    data: bytes

    AVP_HEADER_LENGTH: ClassVar[int] = 8

    def to_bytes(self):
        length = self.AVP_HEADER_LENGTH + len(self.data)
        pad = (4 - (length % 4)) % 4
        header = struct.pack("!I", self.code)
        header += struct.pack("!B", self.flags)
        header += struct.pack("!I", length)[1:]
        return header + self.data + (b"\x00" * pad)

class DiameterRequest:
    def __init__(self, version, command_code):
        self.version = version
        self.command_code = command_code
        self.header = b""
        self.avps = b""
    
    def add_avp(self, code, flags, data):
        if code == AVP_VENDOR_ID or code == AVP_DISCONNECT_CAUSE:
            payload = struct.pack("!I", data)
        else:
            payload = data
        self.avps += DiameterAVP(
            code=code, 
            flags=flags, 
            data=payload
        ).to_bytes()
    
    def build(self):
        self.header = DiameterHeader(
            version=self.version, 
            avps_length=len(self.avps), 
            flags=0x80, 
            command_code=self.command_code,
            application_id=DIAMETER_COMMON_MESSAGES_APPLICATION_ID
        ).to_bytes()
    
    def get_msg(self):
        return self.header + self.avps 
    