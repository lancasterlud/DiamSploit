from dataclasses import dataclass
from typing import ClassVar, Optional
import struct
import random

# Versions
VERSION_ONE = 1

# AVP codes
AVP_USER_NAME           = 1
AVP_RESULT_CODE         = 268
AVP_ORIGIN_HOST         = 264
AVP_ORIGIN_REALM        = 296
AVP_DESTINATION_HOST    = 293
AVP_DESTINATION_REALM   = 283
AVP_VENDOR_ID           = 266
AVP_PRODUCT_NAME        = 269
AVP_SESSION_ID          = 263
AVP_AUTH_SESSION_STATE  = 277

# AVP values
DIAMETER_SUCCESS = b"\x00\x00\x07\xd1"

@dataclass
class DiameterHeader:
    version: int
    avps_length: int
    flags: int
    command_code: int
    application_id: int
    hop_by_hop_id: Optional[int] = None
    end_to_end_id: Optional[int] = None

    HEADER_LENGTH: ClassVar[int] = 20
        
    def to_bytes(self):
        self.hop_by_hop_id = random.randint(1, 0xffffffff) 
        self.end_to_end_id = random.randint(1, 0xffffffff) 
        header = struct.pack("!B", self.version)
        header += struct.pack("!I", self.HEADER_LENGTH + self.avps_length)[1:]
        header += struct.pack("!B", self.flags)
        header += struct.pack("!I", self.command_code)[1:]
        header += struct.pack("!I", self.application_id)
        header += struct.pack("!I", self.hop_by_hop_id)
        header += struct.pack("!I", self.end_to_end_id)
        return header
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "DiameterHeader":
        version = data[0]
        length = struct.unpack("!I", b"\x00" + data[1:4])[0]
        flags = data[4]
        command_code = struct.unpack("!I", b"\x00" + data[5:8])[0]
        application_id = struct.unpack("!I", data[8:12])[0]
        hop_by_hop_id = struct.unpack("!I", data[12:16])[0]
        end_to_end_id = struct.unpack("!I", data[16:20])[0]
        return cls(
            version, 
            length - cls.HEADER_LENGTH, 
            flags, 
            command_code, 
            application_id,
            hop_by_hop_id,
            end_to_end_id
        )

@dataclass
class DiameterAVP:
    code: int
    flags: int
    data: bytes
    length: int = 0
    vendor_id: Optional[int] = None

    AVP_HEADER_LENGTH: ClassVar[int] = 8
    AVP_HEADER_LENGTH_VENDOR: ClassVar[int] = 12

    def get_padding(self):
        return (4 - (self.length % 4)) % 4

    def to_bytes(self):
        if self.flags & 0x80:
            if self.vendor_id is None:
                raise ValueError("Vendor ID must be set when Vendor-Specific flag is used")
            self.length = self.AVP_HEADER_LENGTH_VENDOR + len(self.data)
            header = struct.pack("!I", self.code)
            header += struct.pack("!B", self.flags)
            header += struct.pack("!I", self.length)[1:]
            header += struct.pack("!I", self.vendor_id)
        else:
            self.length = self.AVP_HEADER_LENGTH + len(self.data)
            header = struct.pack("!I", self.code)
            header += struct.pack("!B", self.flags)
            header += struct.pack("!I", self.length)[1:]
        return header + self.data + (b"\x00" * self.get_padding())
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "DiameterAVP":
        code = struct.unpack("!I", data[:4])[0]
        flags = data[4]
        length = struct.unpack("!I", b"\x00" + data[5:8])[0]

        vendor_id = None
        if flags & 0x80:
            vendor_id = struct.unpack("!I", data[8:12])[0]
            avp_data = data[12:length]
        else:
            avp_data = data[8:length]

        return cls(code=code, flags=flags, data=avp_data, length=length, vendor_id=vendor_id)

class DiameterRequest:
    REQUEST_FLAG: ClassVar[int] = 0x80
    REQUEST_PROXIABLE_FLAGS: ClassVar[int] = 0xC0

    def __init__(self, version, command_code, application_id):
        self.version = version
        self.command_code = command_code
        self.application_id = application_id
        self.header = b""
        self.avps = b""
    
    def add_avp(self, code, flags, data, vendor_id=None):
        if vendor_id == None:
            self.avps += DiameterAVP(
                code=code, 
                flags=flags, 
                data=data
            ).to_bytes()
        else:
            self.avps += DiameterAVP(
                code=code, 
                flags=flags, 
                data=data,
                vendor_id=vendor_id
            ).to_bytes()
    
    def build(self, proxyable = False):
        self.header = DiameterHeader(
            version=self.version, 
            avps_length=len(self.avps), 
            flags=(self.REQUEST_PROXIABLE_FLAGS if proxyable else self.REQUEST_FLAG), 
            command_code=self.command_code,
            application_id=self.application_id
        ).to_bytes()
    
    def get_msg(self):
        return self.header + self.avps 
    
class DiameterResponse:
    def __init__(self, raw):
        self.raw = raw
    
    def process(self):
        data = self.raw
        self.header = DiameterHeader.from_bytes(data[:20])
        data = data[20:]
        self.avps = {}
        while len(data) > 0:
            avp = DiameterAVP.from_bytes(data)
            if avp.code in self.avps:
                self.avps[avp.code].append(avp)
            else:
                self.avps[avp.code] = [avp]
            data = data[avp.length + avp.get_padding():]
    
    def success(self):
        if not AVP_RESULT_CODE in self.avps:
            return False
        return self.avps[AVP_RESULT_CODE][0].data == DIAMETER_SUCCESS
