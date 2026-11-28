"""
State               CertificateInstalled
System under test   CSMS
Description         A pre configured certificate of the specified certificateType will be installed.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType <Specified
               certificateType>

1. The CSMS sends a InstallCertificateRequest
2. The Test System responds with a InstallCertificateResponse With status is Accepted

Tool validations
* Step 1: Message: InstallCertificateRequest
  - certificateType must be <Specified certificateType>
  - certificate must be <The configured certificate of the specified certificateType.>
Post condition      Certificate of the specified certificateType is stored at the Charging Station.
"""

from certificates import configured_certificate
from charge_point import TziChargePoint21
from trigger import send_call


async def certificate_installed(cp: TziChargePoint21, certificate_type: str):
    """Returns the InstallCertificateRequest of the CSMS."""
    certificate = configured_certificate(certificate_type)

    # Manual Action: Trigger the CSMS to send an InstallCertificateRequest with certificateType
    #                <Specified certificateType>
    # 1. The CSMS sends a InstallCertificateRequest
    # 2. The Test System responds with a InstallCertificateResponse With status is Accepted
    cp.set_response('InstallCertificate', status='Accepted')
    request = await cp.wait_for_request(
        'InstallCertificate',
        manual_action=send_call(cp.id, 'InstallCertificate', {
            'certificateType': certificate_type,
            'certificate': certificate,
        }))
    assert request.certificate_type == certificate_type, \
        f"Expected InstallCertificateRequest.certificateType {certificate_type}, " \
        f"got {request.certificate_type}"
    assert request.certificate.strip() == certificate.strip(), \
        f"InstallCertificateRequest.certificate is not the configured certificate of " \
        f"{certificate_type}: {request.certificate}"
    return request
