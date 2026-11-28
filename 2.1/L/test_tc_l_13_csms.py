"""
Test case name      Secure Firmware Update - Unable to download/install firmware with ongoing transaction -
                    AllowNewSessionsPendingFirmwareUpdate is false
Test case Id        TC_L_13_CSMS
Use case Id(s)      L01
Requirement(s)      L01.FR.01, L01.FR.11

Requirement Details:
    L01.FR.01: The Charging Station SHALL send a FirmwareStatusNotificationRequest message to the CSMS with
               this new status. What reason to use is described in the description of FirmwareStatusEnumType.
        Precondition: Whenever the Charging Station enters a new state in the firmware update process.
    L01.FR.11: For security purposes the CSMS SHALL include the Firmware Signing certificate (see Keys used in
               OCPP) in the UpdateFirmwareRequest.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to securely download and install a new
                    firmware by sending an UpdateFirmwareRequest with a signingCertificate.

Purpose             To verify if the CSMS is able to handle a Charging Station setting connectors to
                    Unavailable while preparing a firmware update when there is a transaction ongoing.

Prerequisite(s)     The CSMS is able to request a new firmware update when there is a transaction ongoing on
                    the Charging Station.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a UpdateFirmwareRequest
2. The Test System responds with a UpdateFirmwareResponse
    With status Accepted
3. The Test System sends a FirmwareStatusNotificationRequest.
    With status DownloadScheduled
4. The CSMS responds with a FirmwareStatusNotificationResponse.
5. The Test System notifies the CSMS about the state change of all connectors that don’t have a running
   transaction.
    Message: StatusNotificationRequest
    - connectorStatus Unavailable
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Unavailable"
    - component.name "Connector"
    - variable.name "AvailabilityState"
6. The CSMS responds accordingly.
7. Execute Reusable State StopAuthorized
    Note(s) Wait <configured transaction duration> before executing this step
8. Execute Reusable State EVConnectedPostSession
9. Execute Reusable State EVDisconnected
10. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloading
    Note(s):
    - This step will be executed after the given retrieveDateTime from step 1 has been reached.
11. The CSMS responds with a FirmwareStatusNotificationResponse.
12. The Test System sends a FirmwareStatusNotificationRequest.
    With status Downloaded
13. The CSMS responds with a FirmwareStatusNotificationResponse.
14. The Test System sends a FirmwareStatusNotificationRequest.
    With status SignatureVerified
15. The CSMS responds with a FirmwareStatusNotificationResponse.
16. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installing
17. The CSMS responds with a FirmwareStatusNotificationResponse.
18. The Test System sends a FirmwareStatusNotificationRequest.
    With status InstallRebooting
19. The CSMS responds with a FirmwareStatusNotificationResponse.
20. The Test System sends a BootNotificationRequest
    With reason FirmwareUpdate
21. The CSMS responds with a BootNotificationResponse
22. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
23. The CSMS responds accordingly.
24. The Test System sends a FirmwareStatusNotificationRequest.
    With status Installed
25. The CSMS responds with a FirmwareStatusNotificationResponse.

Tool validations
* Step 1:
    Message UpdateFirmwareRequest
    - firmware.signingCertificate <configured signingCertificate>
* Step 19:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.15. Page 415 - (2026-04) - L01.FR.04 - removed ECSchnorr algorithm option and clarify the signature
        verification the Charging Station must do
        (Part 2 errata - applies to this test via use case L01)
        |  | ID. | Precondition | Requirements | Note |
        | Old | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          signature SHALL be validated, by calculating the signature over the entire firmware file using the
          RSA-PSS or ECSchnorr algorithm for signing, and the SHA256 algorithm for calculating hash values. |
          |
        | New | L01.FR.04 | When the Charging Station has successfully downloaded the new firmware | The
          charging station SHALL verify the signature from the UpdateFirmwareRequest with the hash over the
          entire received firmware file computed using the signature hash algorithm. | The RSA-PSS or ECDSA
          algorithm is used for signing. Please refer to section [certificate_properties] for more details
          about signature algorithms and computing hash values. |
"""

import asyncio
import os

import pytest

from charge_point import CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from firmware import (
    reboot_with_new_firmware,
    request_firmware_update,
    seconds_until,
    signing_certificate,
)
from reusable_states.booted import booted
from reusable_states.energy_transfer_started import energy_transfer_started
from reusable_states.ev_connected_post_session import ev_connected_post_session
from reusable_states.ev_disconnected import ev_disconnected
from reusable_states.stop_authorized import stop_authorized
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])
TRANSACTION_DURATION = int(os.environ['TRANSACTION_DURATION'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_13(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: The CSMS is able to request a new firmware update when there is a transaction
    # ongoing on the Charging Station.
    # Reusable State: State is EnergyTransferStarted
    await energy_transfer_started(cp)

    # 1. The CSMS sends a UpdateFirmwareRequest
    # 2. The Test System responds with a UpdateFirmwareResponse With status Accepted
    # The firmware is to be retrieved when the transaction has ended.
    request = await request_firmware_update(cp, retrieve_in=TRANSACTION_DURATION + 2)
    assert request.firmware.signing_certificate == signing_certificate(), \
        f"Expected firmware.signingCertificate <configured signingCertificate>, " \
        f"got {request.firmware.signing_certificate}"

    # 3. The Test System sends a FirmwareStatusNotificationRequest. With status DownloadScheduled
    # 4. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request(
        'DownloadScheduled', request_id=request.request_id)

    # 5. The Test System notifies the CSMS about the state change of all connectors that don't
    #    have a running transaction.
    #    Message: StatusNotificationRequest - connectorStatus Unavailable
    #    Message: NotifyEventRequest - trigger Delta, actualValue "Unavailable", component.name
    #             "Connector", variable.name "AvailabilityState"
    # 6. The CSMS responds accordingly.
    for evse_id in range(1, CONFIGURED_NUMBER_OF_EVSES + 1):
        if evse_id != CONFIGURED_EVSE_ID:
            await cp.send_connector_status('Unavailable', evse_id=evse_id,
                                           connector_id=CONFIGURED_CONNECTOR_ID)

    # 7. Execute Reusable State StopAuthorized
    #    Note(s) Wait <configured transaction duration> before executing this step (the wait of
    #    the state itself)
    await stop_authorized(cp)

    # 8. Execute Reusable State EVConnectedPostSession
    await ev_connected_post_session(cp)

    # 9. Execute Reusable State EVDisconnected
    await ev_disconnected(cp)

    # 10. The Test System sends a FirmwareStatusNotificationRequest. With status Downloading
    #     Note(s): This step will be executed after the given retrieveDateTime from step 1 has
    #     been reached.
    # 11. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 12. ... With status Downloaded
    # 13. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 14. ... With status SignatureVerified
    # 15. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 16. ... With status Installing
    # 17. The CSMS responds with a FirmwareStatusNotificationResponse.
    # 18. ... With status InstallRebooting
    # 19. The CSMS responds with a FirmwareStatusNotificationResponse.
    await asyncio.sleep(max(0.0, seconds_until(request.firmware.retrieve_date_time)))
    for status in ('Downloading', 'Downloaded', 'SignatureVerified', 'Installing', 'InstallRebooting'):
        await cp.send_firmware_status_notification_request(status, request_id=request.request_id)

    # 20. The Test System sends a BootNotificationRequest With reason FirmwareUpdate
    # 21. The CSMS responds with a BootNotificationResponse - status Accepted
    # 22. The Test System notifies the CSMS about the current state of all connectors.
    #     Message: StatusNotificationRequest - connectorStatus Available
    #     Message: NotifyEventRequest - trigger Delta, actualValue "Available", component.name
    #              "Connector", variable.name "AvailabilityState"
    # 23. The CSMS responds accordingly.
    await reboot_with_new_firmware(cp)

    # 24. The Test System sends a FirmwareStatusNotificationRequest. With status Installed
    # 25. The CSMS responds with a FirmwareStatusNotificationResponse.
    await cp.send_firmware_status_notification_request('Installed', request_id=request.request_id)

    start_task.cancel()
