"""
Test case name      Set new NetworkConnectionProfile - Accepted
Test case Id        TC_B_42_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.01

Requirement Details:
    B09.FR.01: On receipt of the SetNetworkProfileRequest The Charging Station SHALL validate the content, store the new data and if successful, respond by sending a SetNetworkProfileResponse message, with status Accepted Matches B09.FR.33 for NetworkConfiguration.
        Precondition: On receipt of the SetNetworkProfileRequest
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in preparation of a
                    migration to a new CSMS.
Purpose             To verify if the CSMS is able to set a new network connection profile at one of the by the
                    Charging Station defined configuration slots.

Prerequisite(s)     N/a

Test Scenario
1. The CSMS sends a SetNetworkProfileRequest
2. The OCTT responds with a SetNetworkProfileResponse with status Accepted

Tool validations
* Step 1:
    Message: SetNetworkProfileRequest
    - configurationSlot is <Configured configurationSlot>
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppCsmsUrl <Configured ocppCsmsUrl>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile>

Post scenario validations:
    - N/a
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType,
    SetNetworkProfileStatusEnumType
)

from tzi_charge_point import TziChargePoint
from trigger import send_call
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])
CONFIGURED_CONFIGURATION_SLOT = os.environ['CONFIGURED_CONFIGURATION_SLOT']
CONFIGURED_MESSAGE_TIMEOUT = os.environ['CONFIGURED_MESSAGE_TIMEOUT']
CONFIGURED_OCPP_CSMS_URL = os.environ['CSMS_ADDRESS']
CONFIGURED_OCPP_INTERFACE = os.environ['CONFIGURED_OCPP_INTERFACE']
CONFIGURED_SECURITY_PROFILE = os.environ['CONFIGURED_SECURITY_PROFILE']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_42(connection):
    """Set new NetworkConnectionProfile - Accepted: CSMS sets network connection profile."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._set_network_profile_response_status = SetNetworkProfileStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Step 1-2: Trigger CSMS to send SetNetworkProfileRequest
    trigger_task = asyncio.create_task(send_call(
        BASIC_AUTH_CP, "SetNetworkProfile", {
            "configurationSlot": int(CONFIGURED_CONFIGURATION_SLOT),
            "connectionData": {
                "messageTimeout": int(CONFIGURED_MESSAGE_TIMEOUT),
                "ocppCsmsUrl": CONFIGURED_OCPP_CSMS_URL,
                "ocppInterface": CONFIGURED_OCPP_INTERFACE,
                "ocppTransport": "JSON",
                "ocppVersion": "OCPP20",
                "securityProfile": int(CONFIGURED_SECURITY_PROFILE),
            },
        },
    ))

    await asyncio.wait_for(
        cp._received_set_network_profile.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    assert cp._set_network_profile_data is not None

    # Validate configurationSlot is present
    config_slot = cp._set_network_profile_data['configuration_slot']
    assert config_slot is not None, "configurationSlot must be present"
    if CONFIGURED_CONFIGURATION_SLOT is not None:
        assert int(config_slot) == int(CONFIGURED_CONFIGURATION_SLOT), \
            f"Expected configurationSlot {CONFIGURED_CONFIGURATION_SLOT}, got: {config_slot}"
    logging.info(f"SetNetworkProfileRequest: configurationSlot={config_slot}")

    # Validate connectionData fields
    conn_data = cp._set_network_profile_data['connection_data']
    assert conn_data is not None, "connectionData must be present"

    # ocppTransport must be JSON
    ocpp_transport = conn_data.get('ocpp_transport', conn_data.get('ocppTransport'))
    assert ocpp_transport == 'JSON', \
        f"Expected ocppTransport = JSON, got: {ocpp_transport}"

    # ocppVersion must be OCPP20
    ocpp_version = conn_data.get('ocpp_version', conn_data.get('ocppVersion'))
    assert ocpp_version == 'OCPP20', \
        f"Expected ocppVersion = OCPP20, got: {ocpp_version}"

    # ocppCsmsUrl must be present
    ocpp_csms_url = conn_data.get('ocpp_csms_url', conn_data.get('ocppCsmsUrl'))
    assert ocpp_csms_url is not None, "connectionData.ocppCsmsUrl must be present"

    # ocppInterface must be present
    ocpp_interface = conn_data.get('ocpp_interface', conn_data.get('ocppInterface'))
    assert ocpp_interface is not None, "connectionData.ocppInterface must be present"

    # messageTimeout must be present
    message_timeout = conn_data.get('message_timeout', conn_data.get('messageTimeout'))
    assert message_timeout is not None, "connectionData.messageTimeout must be present"
    if CONFIGURED_MESSAGE_TIMEOUT is not None:
        assert int(message_timeout) == int(CONFIGURED_MESSAGE_TIMEOUT), \
            f"Expected messageTimeout {CONFIGURED_MESSAGE_TIMEOUT}, got: {message_timeout}"

    # securityProfile must be present
    security_profile = conn_data.get('security_profile', conn_data.get('securityProfile'))
    assert security_profile is not None, "connectionData.securityProfile must be present"
    if CONFIGURED_SECURITY_PROFILE is not None:
        assert int(security_profile) == int(CONFIGURED_SECURITY_PROFILE), \
            f"Expected securityProfile {CONFIGURED_SECURITY_PROFILE}, got: {security_profile}"
    if CONFIGURED_OCPP_CSMS_URL is not None:
        assert ocpp_csms_url == CONFIGURED_OCPP_CSMS_URL, \
            f"Expected ocppCsmsUrl {CONFIGURED_OCPP_CSMS_URL}, got: {ocpp_csms_url}"
    if CONFIGURED_OCPP_INTERFACE is not None:
        assert ocpp_interface == CONFIGURED_OCPP_INTERFACE, \
            f"Expected ocppInterface {CONFIGURED_OCPP_INTERFACE}, got: {ocpp_interface}"

    logging.info(f"SetNetworkProfileRequest validated: slot={config_slot}, "
                 f"url={ocpp_csms_url}, interface={ocpp_interface}, "
                 f"transport={ocpp_transport}, version={ocpp_version}, "
                 f"timeout={message_timeout}, security={security_profile}")

    start_task.cancel()
