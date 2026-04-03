from diameter import *
import struct

# Application ID
S6c_3GPP = 16777312

# Command codes
SRR_COMMAND_CODE = 8388647

# AVP codes
AVP_MSISDN      = 701
AVP_SC_ADDRESS  = 3300

# AVP values
NO_STATE_MAINTAINED = 1

# Vendor ID
VENDOR_ID_3GPP = 10415

def tbcd_encode(number: str) -> bytes:
    if len(number) % 2 != 0:
        number += 'F'

    result = bytearray()

    for i in range(0, len(number), 2):
        low = number[i]
        high = number[i+1]
        byte = int(high + low, 16)
        result.append(byte)

    return bytes(result)

class SendRoutingInfoForSMRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, SRR_COMMAND_CODE, S6c_3GPP)
    
    def session_id(self, session_id):
        super().add_avp(AVP_SESSION_ID, 0x40, session_id)

    def auth_session_state(self):
        super().add_avp(AVP_AUTH_SESSION_STATE, 0x40, struct.pack("!I", NO_STATE_MAINTAINED))
    
    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)

    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    
    def destination_realm(self, destination_realm):
        super().add_avp(AVP_DESTINATION_REALM, 0x40, destination_realm)
    
    def destination_host(self, destination_host):
        super().add_avp(AVP_DESTINATION_HOST, 0x40, destination_host)

    def msisdn(self, msisdn: str):
        super().add_avp(AVP_MSISDN, 0xC0, tbcd_encode(msisdn), vendor_id=VENDOR_ID_3GPP)

    def sc_address(self, sc_address: str):
        super().add_avp(AVP_SC_ADDRESS, 0xC0, tbcd_encode(sc_address), vendor_id=VENDOR_ID_3GPP)
    
    def build(self):
        super().build(proxyable=True)
