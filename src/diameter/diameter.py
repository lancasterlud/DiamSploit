from dataclasses import dataclass
from typing import ClassVar
import struct
import random

# Versions
VERSION_ONE = 1

# AVP codes
AVP_ORIGIN_HOST   = 264
AVP_ORIGIN_REALM  = 296
AVP_VENDOR_ID     = 266
AVP_PRODUCT_NAME  = 269

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
    REQUEST_FLAG: ClassVar[int] = 0x80

    def __init__(self, version, command_code, application_id):
        self.version = version
        self.command_code = command_code
        self.application_id = application_id
        self.header = b""
        self.avps = b""
    
    def add_avp(self, code, flags, data):
        self.avps += DiameterAVP(
            code=code, 
            flags=flags, 
            data=data
        ).to_bytes()
    
    def build(self):
        self.header = DiameterHeader(
            version=self.version, 
            avps_length=len(self.avps), 
            flags=self.REQUEST_FLAG, 
            command_code=self.command_code,
            application_id=self.application_id
        ).to_bytes()
    
    def get_msg(self):
        return self.header + self.avps 
    