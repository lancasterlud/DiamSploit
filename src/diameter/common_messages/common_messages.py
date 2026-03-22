from diameter import *
import struct

# Application ID
DIAMETER_COMMON_MESSAGES = 0

# Command codes
CER_COMMAND_CODE = 257
DWR_COMMAND_CODE = 280
DPR_COMMAND_CODE = 282

# AVP codes
AVP_DISCONNECT_CAUSE = 273

# Disconnect-Cause codes
DISCONNECT_CAUSE_REBOOTING = 0
DISCONNECT_CAUSE_BUSY = 1
DISCONNECT_CAUSE_DO_NOT_WANT_TO_TALK_TO_YOU = 2

class CapabilitiesExchangeRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, CER_COMMAND_CODE, DIAMETER_COMMON_MESSAGES)
    
    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    
    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)

    def vendor_id(self, vendor_id):
        super().add_avp(AVP_VENDOR_ID, 0x40, struct.pack("!I", vendor_id))

    def product_name(self, product_name):
        super().add_avp(AVP_PRODUCT_NAME, 0x00, product_name)

class DeviceWatchdogRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, DWR_COMMAND_CODE, DIAMETER_COMMON_MESSAGES)

    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    
    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)

class DisconnectPeerRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, DPR_COMMAND_CODE, DIAMETER_COMMON_MESSAGES)
 
    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)
    
    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    
    def disconnect_cause(self, disconnect_cause):
        super().add_avp(AVP_DISCONNECT_CAUSE, 0x40, struct.pack("!I", disconnect_cause))
