"""
Test case name      Update Charging Station Certificate by request of CSMS - Invalid certificate
Test case Id        TC_A_14_CSMS
Use case Id(s)      A02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station
                    certificate using the TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to handle a Charging Station rejecting the new Charging
                    Station certificate.

Prerequisite(s)     The CSMS supports security profile 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse
    - status Accepted
3. The Test System sends a SignCertificateRequest
    - csr <Configured CSR>
    - certificateType ChargingStationCertificate
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
6. The Test System responds with a CertificateSignedResponse
    - status Rejected
7. The Test System sends a SecurityEventNotificationRequest
    - type = InvalidChargingStationCertificate
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

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.7. Page 37 - (2026-02) - A02.FR.02 - Requirement reference correction
        (Part 2 errata - applies to this test via use case A02)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 4.2.1.3 of [16]. | |
        | New | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 8.1 of [27] . | |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from security import connect_with_profile, station_csr
from trigger import trigger_v21

SECURITY_PROFILE_3_CP = os.environ['CP21_SP3']


@pytest.mark.asyncio
async def test_tc_a_14():
    cp_id = SECURITY_PROFILE_3_CP

    ws = await connect_with_profile(cp_id, security_profile=3)
    try:
        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 1. The CSMS sends a TriggerMessageRequest
        # 2. The Test System responds with a TriggerMessageResponse - status Accepted
        trigger_message = await cp.wait_for_request(
            'TriggerMessage',
            manual_action=trigger_v21(cp_id, 'trigger-message',
                                      {'requestedMessage': 'SignChargingStationCertificate'}))
        assert trigger_message.requested_message == 'SignChargingStationCertificate', \
            f"Expected requestedMessage SignChargingStationCertificate, got: {trigger_message.requested_message}"

        # The CSMS may send its CertificateSignedRequest right after its SignCertificateResponse,
        # so the station's answer of step 6 is set before step 3.
        cp.set_response('CertificateSigned', status='Rejected')

        # 3. The Test System sends a SignCertificateRequest
        #    - csr <Configured CSR>
        #    - certificateType ChargingStationCertificate
        # 4. The CSMS responds with a SignCertificateResponse
        csr, _ = station_csr(cp_id)
        sign_response = await cp.call(call.SignCertificate(
            csr=csr,
            certificate_type='ChargingStationCertificate',
        ))
        assert sign_response.status == 'Accepted', \
            f"Expected SignCertificateResponse.status Accepted, got: {sign_response.status}"

        # 5. The CSMS sends a CertificateSignedRequest
        # 6. The Test System responds with a CertificateSignedResponse - status Rejected
        await cp.wait_for_request('CertificateSigned')

        # 7. The Test System sends a SecurityEventNotificationRequest
        #    - type = InvalidChargingStationCertificate
        # 8. The CSMS responds with a SecurityEventNotificationResponse
        await cp.send_security_event_notification('InvalidChargingStationCertificate')

        start_task.cancel()
    finally:
        await ws.close()
