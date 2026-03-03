"""
Test case name      Update Charging Station Certificate by request of CSMS - Invalid certificate
Test case Id        TC_A_14_CSMS
Use case Id(s)      A02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station certificate using the
                    TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to handle a Charging Station rejecting the new Charging Station
                    certificate.

Prerequisite(s)     The CSMS supports security profile 3

Test Scenario
1. The CSMS sends a TriggerMessageRequest
    With requestedMessage SignChargingStationCertificate
2. The OCTT responds with a TriggerMessageResponse
    With status Accepted
3. The OCTT sends a SignCertificateRequest
    With csr <Configured CSR>
    certificateType ChargingStationCertificate
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
6. The OCTT responds with a CertificateSignedResponse
    With status Rejected
7. The OCTT sends a SecurityEventNotificationRequest
    with type = InvalidChargingStationCertificate
8. The CSMS responds with a SecurityEventNotificationResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage SignChargingStationCertificate

* Step 4:
    Message: SignCertificateResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os
import time
import logging

import pytest
import websockets

from ocpp.v201.enums import (
    GenericStatusEnumType, CertificateSignedStatusEnumType,
    CertificateSigningUseEnumType
)

from tzi_charge_point import TziChargePoint
from trigger import trigger_v201
from utils import create_ssl_context, generate_csr, now_iso

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_3_CP = os.environ['CP201_SP3']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_a_14():
    cp_id = SECURITY_PROFILE_3_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'
    ssl_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT,
        client_key=TLS_CLIENT_KEY,
    )
    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    cp = TziChargePoint(cp_id, ws)
    # Step 6: Configure to REJECT the signed certificate
    cp._certificate_signed_response_status = CertificateSignedStatusEnumType.rejected
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Trigger CSMS to send TriggerMessageRequest(SignChargingStationCertificate)
    asyncio.create_task(trigger_v201(cp_id, 'trigger-message', {
        'requestedMessage': 'SignChargingStationCertificate',
    }))

    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._trigger_message_data == 'SignChargingStationCertificate', \
        f"Expected SignChargingStationCertificate, got: {cp._trigger_message_data}"

    # Step 3-4: Send SignCertificateRequest
    csr_pem, _ = generate_csr(cp_id)
    sign_response = await cp.send_sign_certificate_request(
        csr=csr_pem,
        certificate_type=CertificateSigningUseEnumType.charging_station_certificate,
    )
    assert sign_response.status == GenericStatusEnumType.accepted, \
        f"Expected SignCertificateResponse Accepted, got: {sign_response.status}"

    # Step 5-6: Wait for CSMS to send CertificateSignedRequest - CS will reject it
    await asyncio.wait_for(
        cp._received_certificate_signed.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._certificate_signed_data is not None
    cert_type = cp._certificate_signed_data.get('certificate_type')
    assert cert_type in (
        CertificateSigningUseEnumType.charging_station_certificate,
        'ChargingStationCertificate',
    ), f"Expected certificateType ChargingStationCertificate, got: {cert_type}"

    # Step 7-8: Send SecurityEventNotification(type=InvalidChargingStationCertificate).
    security_event_response = await cp.send_security_event_notification(
        event_type='InvalidChargingStationCertificate',
        timestamp=now_iso(),
    )
    assert security_event_response is not None
    logging.info("Received CertificateSignedRequest from CSMS - responded with Rejected and sent security event")

    start_task.cancel()
    await ws.close()
