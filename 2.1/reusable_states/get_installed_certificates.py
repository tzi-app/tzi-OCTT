"""
State               GetInstalledCertificates
System under test   CSMS
Description         The hashData from installed certificates of the specified type will be retrieved from the
                    Charging Station
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with certificateType _<Specified
               certificateType>

1. The CSMS sends a GetInstalledCertificateIdsRequest
2. The Test System responds with a GetInstalledCertificateIdsResponse With status is Accepted
   certificateHashDataChain contains an entry with following values:
   certificateHashDataChain[0].certificateType is <Specified certificateType>
   certificateHashDataChain[0].certificateHashData contains <HashData from the configured certificate of the
   specified certificateType>

Tool validations
* Step 1: Message: GetInstalledCertificateIdsRequest - certificateType must be <Specified certificateType>
Post condition      Certificate of the specified certificateType is retrieved from the Charging Station.
"""

from certificates import certificate_hash_data_chain
from charge_point import TziChargePoint21
from trigger import send_call


async def get_installed_certificates(cp: TziChargePoint21, *certificate_types: str,
                                     hash_algorithm: str = 'SHA256'):
    """certificate_types: the specified certificateType, or more than one.
    hash_algorithm: the algorithm with which the Test System hashes the data of its response.
    Returns the hash data that the Test System responded with: a certificateHashDataChain.
    """
    chain = [certificate_hash_data_chain(certificate_type, hash_algorithm)
             for certificate_type in certificate_types]

    # Manual Action: Trigger the CSMS to send a GetInstalledCertificateIdsRequest with
    #                certificateType <Specified certificateType>
    # 1. The CSMS sends a GetInstalledCertificateIdsRequest
    # 2. The Test System responds with a GetInstalledCertificateIdsResponse With status is
    #    Accepted. certificateHashDataChain contains an entry with following values:
    #    certificateHashDataChain[0].certificateType is <Specified certificateType>
    #    certificateHashDataChain[0].certificateHashData contains <HashData from the configured
    #    certificate of the specified certificateType>
    cp.set_response('GetInstalledCertificateIds', status='Accepted',
                    certificate_hash_data_chain=chain)
    request = await cp.wait_for_request(
        'GetInstalledCertificateIds',
        manual_action=send_call(cp.id, 'GetInstalledCertificateIds',
                                {'certificateType': list(certificate_types)}))
    assert sorted(request.certificate_type or []) == sorted(certificate_types), \
        f"Expected GetInstalledCertificateIdsRequest.certificateType {list(certificate_types)}, " \
        f"got {request.certificate_type}"
    return chain
