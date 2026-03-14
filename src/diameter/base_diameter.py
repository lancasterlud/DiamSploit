from dataclasses import dataclass
import struct
import random

# Command codes
CER_COMMAND_CODE = 257
DWR_COMMAND_CODE = 280

@dataclass
class DiameterHeader:
    version: int
    length: int
    request: bool
    command_code: int
    application_id: int
        
    def to_bytes(self):
        header = struct.pack("!B", self.version)
        header += struct.pack("!I", 20 + self.length)[1:]
        header += struct.pack("!B", 0x80 if self.request else 0x0)
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

    def to_bytes(self):
        length = 8 + len(self.data)
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
        self.avps += DiameterAVP(code, flags, data).to_bytes()
    
    def build(self):
        self.header = DiameterHeader(self.version, 
            len(self.avps), 
            True, 
            self.command_code,
            0
        ).to_bytes()
    
    def get_msg(self):
        return self.header + self.avps 
    