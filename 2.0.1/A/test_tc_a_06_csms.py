"""
Test case name      TLS - server-side certificate - TLS version too low
Test case Id        TC_A_06_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.314, A00.FR.315, A00.FR.409, A00.FR.416, A00.FR.417, A00.FR.418

Requirement Details:
    A00.FR.314: Both of these endpoints SHALL check the version of TLS used. A. Security 21/491 Part 2 - Specification
    A00.FR.315: A00.FR.314 AND The CSMS detects that the Charging Station only allows connections using an older version of TLS, or only allows SSL
        Precondition: A00.FR.314 AND The CSMS detects that the Charging Station only allows connections using an older version of TLS, or only allows SSL
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.416: The Charging Station and CSMS SHALL only use TLS v1.2 or above. (Same as A00.FR.313)
    A00.FR.417: Both of these endpoints SHALL check the version of TLS used. (Same as
    A00.FR.418: A00.FR.417 AND The CSMS detects that the Charging Station only allows connections using an older version of TLS, or only allows SSL
        Precondition: A00.FR.417 AND The CSMS detects that the Charging Station only allows connections using an older version of TLS, or only allows SSL
System under test   CSMS

Description         The CSMS uses a server-side certificate to identify itself to the Charging Station, when using
                    security profile 2 or 3.

Purpose             To verify whether the CSMS is able to terminate the connection when it notices the used TLS version
                    is lower than 1.2.

Prerequisite(s)     The CSMS supports security profile 2 and/or 3

Test Scenario
1. The OCTT terminates the connection and initiates a TLS handshake with a TLS version lower than 1.2
   and sends a Client Hello to the CSMS.
2. The CSMS notices that the TLS version is lower than 1.2 and terminates the connection.
3. The OCTT initiates a TLS handshake with TLS version 1.2 or higher and sends a Client Hello to the CSMS.
4. The CSMS responds with a Server Hello with the <Configured server certificate>
5. The OCTT performs the following actions:
    Send client certificate
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished

    Note(s):
    - The client certificate is only sent when the CSMS uses security profile 3.

6. The CSMS performs the following actions:
    Change Cipher Spec
    Finished

7. The OCTT sends a HTTP upgrade request to the CSMS
    Note(s):
    - The HTTP request only contains a username/password combination when the CSMS uses security profile 2.

8. The CSMS upgrades the connection to a (secured) WebSocket connection.
9. The OCTT sends a BootNotificationRequest with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
10. The CSMS responds with a BootNotificationResponse
11. The OCTT notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
12. The CSMS responds accordingly.

Tool validations
* Step 10:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os
import ssl
import time
import logging

import pytest
import websockets

from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from utils import get_basic_auth_headers, create_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_2_CP = os.environ['CP201_SP2']
SECURITY_PROFILE_3_CP = os.environ['CP201_SP3']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("security_profile", [2, 3])
async def test_tc_a_06(security_profile):
    if security_profile == 2:
        cp_id = SECURITY_PROFILE_2_CP
        headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
    else:
        cp_id = SECURITY_PROFILE_3_CP
        headers = {}

    uri = f'{CSMS_ADDRESS}/{cp_id}'

    # Step 1-2: Attempt connection with TLS version lower than 1.2
    low_tls_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT if security_profile == 3 else None,
        client_key=TLS_CLIENT_KEY if security_profile == 3 else None,
        max_tls_version=ssl.TLSVersion.TLSv1_1,
        check_hostname=False,
    )

    with pytest.raises(ssl.SSLError):
        await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=low_tls_ctx,
        )

    logging.info("CSMS correctly rejected TLS < 1.2 connection")

    # Step 3-8: Connect with TLS 1.2+
    ssl_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT if security_profile == 3 else None,
        client_key=TLS_CLIENT_KEY if security_profile == 3 else None,
    )

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        extra_headers=headers,
        ssl=ssl_ctx,
    )

    time.sleep(0.5)

    # Step 9-12: Boot + Status + NotifyEvent
    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # B01.FR.12: For SP3, serialNumber must match the client certificate CN
    # (which equals the station external_id). Without it, CSMS closes the connection.
    if security_profile == 3:
        boot_response = await cp.send_boot_notification_with_serial(cp_id)
    else:
        boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)
    await cp.send_notify_event([{
        'event_id': 1,
        'timestamp': '2024-01-01T00:00:00Z',
        'trigger': 'Delta',
        'actual_value': 'Available',
        'event_notification_type': 'HardWiredNotification',
        'component': {'name': 'Connector'},
        'variable': {'name': 'AvailabilityState'},
    }])

    start_task.cancel()
    await ws.close()
