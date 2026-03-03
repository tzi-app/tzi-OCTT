"""
Test case name      TLS - Client-side certificate - Invalid certificate
Test case Id        TC_A_08_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.405, A00.FR.407, A00.FR.409, A00.FR.410

Requirement Details:
    A00.FR.405: The CSMS SHALL verify that the certificate belongs to this Charging Station by checking that the CN (commonName) RDN in the subject field of the certificate contains the unique serial number of the Charging Station (see Certificate Properties).
    A00.FR.407: NOT A00.FR.429 AND If the Charging Station does not own a valid certificate, or if the certification path is invalid The CSMS SHALL terminate the connection.
        Precondition: NOT A00.FR.429 AND If the Charging Station does not own a valid certificate, or if the certification path is invalid
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.410: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate. (Same as A00.FR.307)
System under test   CSMS

Description         The Charging Station uses a client-side certificate to identify itself to the CSMS, when using
                    security profile 3.

Purpose             To verify whether the CSMS is able to terminate the connection when the received client certificate
                    is invalid.

Prerequisite(s)     - The CSMS supports security profile 3
                    - This testcase can be executed multiple times, using different kinds of invalid certificates:
                      Unknown certificate
                      expired certificate
                      certificate with commonName that does not equal the serial number of the Charging Station.

Test Scenario
1. The OCTT initiates a TLS handshake and sends a Client Hello to the CSMS.
2. The CSMS responds with a Server Hello with a server certificate
3. The OCTT performs the following actions:
    Send <Configured invalid client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
4. The CSMS deems the client certificate invalid and terminates the connection.
5. The OCTT initiates a TLS handshake and sends a Client Hello to the CSMS.
6. The CSMS responds with a Server Hello with a server certificate
7. The OCTT performs the following actions:
    Send <Configured client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
8. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
9. The OCTT sends a HTTP upgrade request to the CSMS
10. The CSMS upgrades the connection to a (secured) WebSocket connection.
11. The OCTT sends a BootNotificationRequest with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
12. The CSMS responds with a BootNotificationResponse
13. The OCTT notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
14. The CSMS responds accordingly.

Tool validations
* Step 12:
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
from websockets.exceptions import InvalidMessage

from tzi_charge_point import TziChargePoint
from utils import create_ssl_context

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
TLS_INVALID_CLIENT_CERT = os.environ['TLS_INVALID_CLIENT_CERT']
TLS_INVALID_CLIENT_KEY = os.environ['TLS_INVALID_CLIENT_KEY']
SECURITY_PROFILE_3_CP = os.environ['CP201_SP3']


@pytest.mark.asyncio
async def test_tc_a_08():
    cp_id = SECURITY_PROFILE_3_CP
    uri = f'{CSMS_ADDRESS}/{cp_id}'

    # Step 1-4: Connect with invalid client certificate - CSMS should reject
    invalid_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_INVALID_CLIENT_CERT,
        client_key=TLS_INVALID_CLIENT_KEY,
    )

    with pytest.raises((ssl.SSLError, websockets.InvalidStatusCode, ConnectionResetError, InvalidMessage)):
        await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            ssl=invalid_ctx,
        )

    logging.info("CSMS correctly rejected invalid client certificate")

    # Step 5-10: Connect with valid client certificate
    valid_ctx = create_ssl_context(
        ca_cert=TLS_CA_CERT,
        client_cert=TLS_CLIENT_CERT,
        client_key=TLS_CLIENT_KEY,
    )

    ws = await websockets.connect(
        uri=uri,
        subprotocols=['ocpp2.0.1'],
        ssl=valid_ctx,
    )

    time.sleep(0.5)

    # Step 11-14: Boot + Status + NotifyEvent
    cp = TziChargePoint(cp_id, ws)
    start_task = asyncio.create_task(cp.start())

    # B01.FR.12: For SP3, serialNumber must match the client certificate CN
    boot_response = await cp.send_boot_notification_with_serial(cp_id)
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
