"""
ADDED by OCPP 2.1 Edition 2 errata 2026-09 (5.3, 6.1.1) - transcribed from the errata document.

Test case name      Update Charging Station Certificate by request of CSMS - Success - Charging Station
                    Certificate - with requestId
Test case Id        TC_A_111_CSMS
Use case Id(s)      A02 & F06
Requirement(s)      A02.FR.11, A02.FR.14, F06.FR.01

Requirement Details:
    A02.FR.11: The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
    A02.FR.14: It is RECOMMENDED for the CSMS to set the certificateType field in the CertificateSignedRequest
               to the type of certificate in the SignCertificateRequest.
        Precondition: When receiving a SignCertificateRequest with certificateType included
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station
                    certificate using the TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update its Charging
                    Station Certificate.

Prerequisite(s)     The CSMS supports security profile 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State RenewChargingStationCertificate (With requestId)
2. The Test System disconnects its current connection and reconnects to the CSMS with the new certificate.
3. The CSMS accepts the incoming connection request using the new certificate.

Tool validations
N/a

Post scenario validations:
    The Test System and the CSMS are connected.
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.renew_charging_station_certificate import renew_charging_station_certificate
from security import client_certificate_files, connect_with_profile

SECURITY_PROFILE_3_CP = os.environ['CP21_SP3']


@pytest.mark.asyncio
async def test_tc_a_111():
    cp_id = SECURITY_PROFILE_3_CP

    ws = await connect_with_profile(cp_id, security_profile=3)
    try:
        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 1. Execute Reusable State RenewChargingStationCertificate (With requestId): the
        #    SignCertificateRequest has a requestId, and the CSMS includes it in the
        #    resulting CertificateSignedRequest (A02.FR.25).
        certificate_chain, private_key = await renew_charging_station_certificate(
            cp, with_request_id=True)

        start_task.cancel()
    finally:
        # 2. The Test System disconnects its current connection ...
        await ws.close()

    # 2. ... and reconnects to the CSMS with the new certificate.
    # 3. The CSMS accepts the incoming connection request using the new certificate.
    with client_certificate_files(certificate_chain, private_key) as (new_cert, new_key):
        ws = await connect_with_profile(
            cp_id, security_profile=3, client_cert=new_cert, client_key=new_key)
        try:
            # Post scenario validation: the Test System and the CSMS are connected.
            assert ws.open, "The CSMS must accept the connection with the new certificate"
        finally:
            await ws.close()
