from diameter import *
import struct

# Application ID
S6a_3GPP = 16777251

# Command codes
AIR_COMMAND_CODE = 318
ULR_COMMAND_CODE = 316

# AVP codes
AVP_RAT_TYPE                             = 1032
AVP_ULR_FLAGS                            = 1405
AVP_REQUESTED_EUTRAN_AUTHENTICATION_INFO = 1408
AVP_VISITED_PLMN_ID                      = 1407
AVP_NUMBER_OF_REQUESTED_VECTORS          = 1410
AVP_IMMEDIATE_RESPONSE_PREFERRED         = 1412
AVP_RE_SYNCHRONIZATION_INFO              = 1411

# AVP values
NO_STATE_MAINTAINED = 1

# Vendor ID
VENDOR_ID_3GPP = 10415

def encode_plmn(mcc: str, mnc: str) -> bytes:
    if len(mcc) != 3:
        raise ValueError("MCC must be 3 digits")
    if len(mnc) == 2:
        mnc = mnc + 'F'  # Aggiungi F come terzo digit
    elif len(mnc) != 3:
        raise ValueError("MNC must be 2 or 3 digits")

    # Octet1: MCC digit2 | MCC digit1
    octet1 = int(mcc[1] + mcc[0], 16)
    # Octet2: MNC digit3 | MCC digit3
    octet2 = int(mnc[2] + mcc[2], 16)
    # Octet3: MNC digit2 | MNC digit1
    octet3 = int(mnc[1] + mnc[0], 16)

    return bytes([octet1, octet2, octet3])

class AuthenticationInformationRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, AIR_COMMAND_CODE, S6a_3GPP)

    def session_id(self, session_id):
        super().add_avp(AVP_SESSION_ID, 0x40, session_id)

    def auth_session_state(self):
        super().add_avp(AVP_AUTH_SESSION_STATE, 0x40, struct.pack("!I", NO_STATE_MAINTAINED))

    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)

    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    
    def destination_host(self, destination_host):
        super().add_avp(AVP_DESTINATION_HOST, 0x40, destination_host)

    def destination_realm(self, destination_realm):
        super().add_avp(AVP_DESTINATION_REALM, 0x40, destination_realm)
    
    def user_name(self, user_name):
        super().add_avp(AVP_USER_NAME, 0x40, user_name)

    def requested_eutran_authentication_info(self, n_vectors, immediate=True, resync=None):
        payload = DiameterAVP(
            code=AVP_NUMBER_OF_REQUESTED_VECTORS,
            flags=0xC0,
            data=struct.pack("!I", n_vectors),
            vendor_id=VENDOR_ID_3GPP
        ).to_bytes()
        if immediate:
            payload += DiameterAVP(
                code=AVP_IMMEDIATE_RESPONSE_PREFERRED,
                flags=0xC0,
                data=struct.pack("!I", 1),
                vendor_id=VENDOR_ID_3GPP
            ).to_bytes()
        if resync is not None:
            rand_16, auts_14 = resync
            assert len(rand_16) == 16 and len(auts_14) == 14
            payload += DiameterAVP(
                code=AVP_RE_SYNCHRONIZATION_INFO,
                flags=0xC0,
                data=(rand_16 + auts_14),
                vendor_id=VENDOR_ID_3GPP
            ).to_bytes()
        super().add_avp(AVP_REQUESTED_EUTRAN_AUTHENTICATION_INFO, 0xC0, payload, vendor_id=VENDOR_ID_3GPP)

    def visited_plmn_id(self, plmn: tuple):        
        super().add_avp(AVP_VISITED_PLMN_ID, 0xC0, encode_plmn(plmn[0], plmn[1]), vendor_id=VENDOR_ID_3GPP)

    def build(self):
        super().build(proxyable=True)

class UpdateLocationRequest(DiameterRequest):
    def __init__(self, version):
        super().__init__(version, ULR_COMMAND_CODE, S6a_3GPP)
    
    def session_id(self, session_id):
        super().add_avp(AVP_SESSION_ID, 0x40, session_id)
    
    def origin_host(self, origin_host):
        super().add_avp(AVP_ORIGIN_HOST, 0x40, origin_host)

    def origin_realm(self, origin_realm):
        super().add_avp(AVP_ORIGIN_REALM, 0x40, origin_realm)
    
    def destination_realm(self, destination_realm):
        super().add_avp(AVP_DESTINATION_REALM, 0x40, destination_realm)
    
    def user_name(self, user_name):
        super().add_avp(AVP_USER_NAME, 0x40, user_name)
    
    def rat_type(self, rat_type):
        super().add_avp(AVP_RAT_TYPE, 0xC0, struct.pack("!I", rat_type), vendor_id=VENDOR_ID_3GPP)

    def ulr_flags(self, ulr_flags):
        super().add_avp(AVP_ULR_FLAGS, 0xC0, struct.pack("!I", ulr_flags), vendor_id=VENDOR_ID_3GPP)
    
    def visited_plmn_id(self, plmn: tuple):        
        super().add_avp(AVP_VISITED_PLMN_ID, 0xC0, encode_plmn(plmn[0], plmn[1]), vendor_id=VENDOR_ID_3GPP)
    
    def build(self):
        super().build(proxyable=True)
