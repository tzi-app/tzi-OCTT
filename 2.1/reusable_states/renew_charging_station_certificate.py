"""
State               RenewChargingStationCertificate
System under test   CSMS
Description         The ChargingStationCertificate is renewed using A02/A03
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Request the CSMS to send a Trigger Message Request with requestedMessage
               SignChargingStationCertificate

1. The CSMS sends a TriggerMessageRequest With requestedMessage SignChargingStationCertificate
2. The Test System sends a TriggerMessageResponse with status Accepted
3 The Test System sends a SignCertificateRequest
4. The CSMS responds with a SignCertificateResponse with status Accepted
5. The CSMS sends a CertificateSignedRequest With certificateChain <Certificate generated from the received
   CSR from step 3 and signed by the configured CSMS Root certificate>
   certificateType ChargingStationCertificate
6. The Test System sends a CertificateSignedResponse with status Accepted

Tool validations
* Step 1: Message: TriggerMessageRequest - requestedMessage must be SignChargingStationCertificate
* Step 4: Message: SignCertificateResponse - status must be Accepted
* Step 5: Message: CertificateSignedRequest
  - certificateChain <Certificate generated from the received CSR from step 3 and signed by the configured
    CSMS Root certificate>
  - certificateType must be ChargingStationCertificate
Post condition      N/a
"""

import os
import random

from ocpp.v21 import call

from charge_point import TziChargePoint21
from security import station_csr, validate_signed_certificate
from trigger import trigger_v21

TLS_CA_CERT = os.environ['TLS_CA_CERT']


async def renew_charging_station_certificate(cp: TziChargePoint21, with_request_id=False):
    """Returns (certificate chain in PEM, private key): the renewed Charging Station
    certificate and the key it is for.

    with_request_id: the SignCertificateRequest has a requestId, which the CSMS has to
    include in its CertificateSignedRequest (A02.FR.25).
    """
    # Manual Action: Request the CSMS to send a Trigger Message Request with requestedMessage
    #                SignChargingStationCertificate
    # 1. The CSMS sends a TriggerMessageRequest With requestedMessage SignChargingStationCertificate
    # 2. The Test System sends a TriggerMessageResponse with status Accepted
    trigger_message = await cp.wait_for_request(
        'TriggerMessage',
        manual_action=trigger_v21(cp.id, 'trigger-message',
                                  {'requestedMessage': 'SignChargingStationCertificate'}))
    assert trigger_message.requested_message == 'SignChargingStationCertificate', \
        f"Expected requestedMessage SignChargingStationCertificate, got: {trigger_message.requested_message}"

    # 3. The Test System sends a SignCertificateRequest
    # 4. The CSMS responds with a SignCertificateResponse with status Accepted
    csr, private_key = station_csr(cp.id)
    request_id = random.randint(1, 2 ** 31 - 1) if with_request_id else None
    sign_response = await cp.call(call.SignCertificate(
        csr=csr,
        certificate_type='ChargingStationCertificate',
        request_id=request_id,
    ))
    assert sign_response.status == 'Accepted', \
        f"Expected SignCertificateResponse.status Accepted, got: {sign_response.status}"

    # 5. The CSMS sends a CertificateSignedRequest
    # 6. The Test System sends a CertificateSignedResponse with status Accepted
    certificate_signed = await cp.wait_for_request('CertificateSigned')
    assert certificate_signed.certificate_type == 'ChargingStationCertificate', \
        f"Expected certificateType ChargingStationCertificate, got: {certificate_signed.certificate_type}"
    # certificateChain: the certificate generated from the received CSR from step 3 and signed
    # by the configured CSMS Root certificate
    validate_signed_certificate(certificate_signed.certificate_chain, private_key, TLS_CA_CERT)
    if with_request_id:
        assert certificate_signed.request_id == request_id, \
            f"Expected the requestId of the SignCertificateRequest ({request_id}), " \
            f"got: {certificate_signed.request_id}"

    return certificate_signed.certificate_chain, private_key
