"""
Test case name      Update Charging Station Certificate by request of CSMS - Success - Combined Certificate
Test case Id        TC_A_13_CSMS
Use case Id(s)      A02
Requirement(s)      A02.FR.11

Requirement Details:
    A02.FR.11: Upon receipt of a SignCertificateRequest AND It is able to process the request The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station certificate using the
                    TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update a its combined V2G / Charging
                    Station Certificate.

Prerequisite(s)     - The CSMS supports security profile 3
                    - The CSMS supports ISO 15118.

Test Scenario
1. The CSMS sends a TriggerMessageRequest
    With requestedMessage SignCombinedCertificate
2. The OCTT responds with a TriggerMessageResponse
    With status Accepted
3. The OCTT sends a SignCertificateRequest
    With csr <Configured CSR>
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
    With certificateChain <Certificate generated from the received CSR from step 3 and signed by the V2G Root or
    SubCA certificate from the configured V2G certificate chain>
6. The OCTT responds with a CertificateSignedResponse
    With status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage SignCombinedCertificate

* Step 4:
    Message: SignCertificateResponse
    - status Accepted

* Step 5:
    Message: CertificateSignedRequest
    - certificateChain <Certificate generated from the received CSR from step 3 and signed by the V2G Root or
      SubCA certificate from the configured V2G certificate chain>

    NOTE: The OCTT will validate the certificate, but if the following validation fail, the testcase will NOT FAIL,
    because generating the certificate is probably not be done by the CSMS.

    - The key must be at least 224 bits long.
    - The received certificate must be transmitted in the X.509 format encoded in Privacy-Enhanced Mail (PEM) format.
    - The certificate must include a serial number.
    - The subject field of the certificate must contain a commonName RDN which consists of the unique serial
      number of the Charging Station.

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
    GenericStatusEnumType, CertificateSignedStatusEnumType
)

from tzi_charge_point import TziChargePoint
from trigger import trigger_v201
from utils import create_ssl_context, generate_csr

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_3_CP = os.environ['CP201_SP3']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
async def test_tc_a_13():
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
    cp._certificate_signed_response_status = CertificateSignedStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Step 1-2: Trigger CSMS to send TriggerMessageRequest(SignCombinedCertificate)
    trigger_task = asyncio.create_task(trigger_v201(cp_id, 'trigger-message', {
        'requestedMessage': 'SignCombinedCertificate',
    }))

    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._trigger_message_data == 'SignCombinedCertificate', \
        f"Expected SignCombinedCertificate, got: {cp._trigger_message_data}"

    # Step 3-4: Send SignCertificateRequest (no specific certificate type for combined)
    csr_pem, _ = generate_csr(cp_id)
    sign_response = await cp.send_sign_certificate_request(csr=csr_pem)
    assert sign_response.status == GenericStatusEnumType.accepted, \
        f"Expected SignCertificateResponse Accepted, got: {sign_response.status}"

    # Step 5-6: Wait for CSMS to send CertificateSignedRequest
    await asyncio.wait_for(
        cp._received_certificate_signed.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    assert cp._certificate_signed_data is not None
    assert cp._certificate_signed_data['certificate_chain'], \
        "CertificateSignedRequest must contain a certificate chain"

    logging.info(f"Received signed combined certificate chain "
                 f"(length={len(cp._certificate_signed_data['certificate_chain'])})")

    start_task.cancel()
    await ws.close()
