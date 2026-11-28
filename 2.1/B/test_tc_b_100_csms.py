"""
Test case name      Set new NetworkConnectionProfile - Identity and password
Test case Id        TC_B_100_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.01, B09.FR.14

Requirement Details:
    B09.FR.01: The Charging Station SHALL validate the content, store the new data and if successful, respond
               by sending a SetNetworkProfileResponse message, with status Accepted
        Precondition: On receipt of the SetNetworkProfileRequest
        Note: Matches B09.FR.33 for NetworkConfiguration.
    B09.FR.14 (2.1): CSMS SHOULD use the SetNetworkProfileRequest to set the Identity or BasicAuthPassword of
                     the Charging Station.
        Note: Alternatively the NetworkConfiguration component can be used, if the corresponding variables are
              writable. See requirements from the "NetworkConfiguration" section below.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify if the CSMS is able to set a new network connection profile that contains
                    basicAuthPassword and identity at one of the by the Charging Station defined configuration
                    slots.

Prerequisite(s)     CSMS uses the SetNetworkProfileRequest to update a network connection profile.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: Request CSMS to send a network profile including identity and password.

1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse
    With status Accepted

Tool validations
* Step 1:
    Message SetNetworkProfileRequest
    - configurationSlot is <Configured configurationSlot>
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppCsmsUrl <Configured ocppCsmsUrl>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile>
    - connectionData.identity <Configured identity>
    - connectionData.basicAuthPassword <Configured basicAuthPassword>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.6. Page 1002 - (2026-02) - TC_B_100_CSMS - Manual action added and tool validations updated
        The note was replaced with a manual action and tool validations were updated.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | [removed: Note: Request CSMS to send a network profile including identity and password.] / Manual
          Action : Request CSMS to send a network profile including identity and password. | |

        | Tool validations |
        | \\* Step 1: / Message SetNetworkProfileRequest / - configurationSlot is <Configured
          configurationSlot> / - connectionData.messageTimeout <Configured messageTimeout> / -
          connectionData.ocppCsmsUrl <Configured ocppCsmsUrl> / - connectionData.ocppInterface <Configured
          ocppInterface> / - connectionData.ocppTransport JSON / - connectionData.ocppVersion [removed:
          OCPP20] OCPP21 / - connectionData.securityProfile [removed: <Configured securityProfile>] <Active
          securityProfile> / - connectionData.identity <Configured identity> / -
          connectionData.basicAuthPassword <Configured basicAuthPassword> |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_CONFIGURATION_SLOT = int(os.environ['CONFIGURED_CONFIGURATION_SLOT'])
CONFIGURED_MESSAGE_TIMEOUT = int(os.environ['CONFIGURED_MESSAGE_TIMEOUT'])
CONFIGURED_OCPP_CSMS_URL = os.environ['CSMS_ADDRESS']
CONFIGURED_OCPP_INTERFACE = os.environ['CONFIGURED_OCPP_INTERFACE']

# The security profile of the station's connection in this test
ACTIVE_SECURITY_PROFILE = 1
CONFIGURED_IDENTITY = BASIC_AUTH_CP
CONFIGURED_BASIC_AUTH_PASSWORD = BASIC_AUTH_CP_PASSWORD


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_100(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Request CSMS to send a network profile including identity and password.
    # 1. The CSMS sends a SetNetworkProfileRequest
    # 2. The Test System responds with a SetNetworkProfileResponse With status Accepted
    request = await cp.wait_for_request(
        'SetNetworkProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'SetNetworkProfile', {
            'configurationSlot': CONFIGURED_CONFIGURATION_SLOT,
            'connectionData': {
                'messageTimeout': CONFIGURED_MESSAGE_TIMEOUT,
                'ocppCsmsUrl': CONFIGURED_OCPP_CSMS_URL,
                'ocppInterface': CONFIGURED_OCPP_INTERFACE,
                'ocppTransport': 'JSON',
                'ocppVersion': 'OCPP21',
                'securityProfile': ACTIVE_SECURITY_PROFILE,
                'identity': CONFIGURED_IDENTITY,
                'basicAuthPassword': CONFIGURED_BASIC_AUTH_PASSWORD,
            },
        }))

    connection_data = request.connection_data
    assert request.configuration_slot == CONFIGURED_CONFIGURATION_SLOT, \
        f"Expected configurationSlot {CONFIGURED_CONFIGURATION_SLOT}, got: {request.configuration_slot}"
    assert connection_data.message_timeout == CONFIGURED_MESSAGE_TIMEOUT, \
        f"Expected messageTimeout {CONFIGURED_MESSAGE_TIMEOUT}, got: {connection_data.message_timeout}"
    assert connection_data.ocpp_csms_url == CONFIGURED_OCPP_CSMS_URL, \
        f"Expected ocppCsmsUrl {CONFIGURED_OCPP_CSMS_URL}, got: {connection_data.ocpp_csms_url}"
    assert connection_data.ocpp_interface == CONFIGURED_OCPP_INTERFACE, \
        f"Expected ocppInterface {CONFIGURED_OCPP_INTERFACE}, got: {connection_data.ocpp_interface}"
    assert connection_data.ocpp_transport == 'JSON', \
        f"Expected ocppTransport JSON, got: {connection_data.ocpp_transport}"
    # Errata 2026-09 (6.3.6): ocppVersion OCPP21, and the active security profile
    assert connection_data.ocpp_version == 'OCPP21', \
        f"Expected ocppVersion OCPP21, got: {connection_data.ocpp_version}"
    assert connection_data.security_profile == ACTIVE_SECURITY_PROFILE, \
        f"Expected securityProfile {ACTIVE_SECURITY_PROFILE}, got: {connection_data.security_profile}"
    assert connection_data.identity == CONFIGURED_IDENTITY, \
        f"Expected identity {CONFIGURED_IDENTITY}, got: {connection_data.identity}"
    assert connection_data.basic_auth_password == CONFIGURED_BASIC_AUTH_PASSWORD, \
        "connectionData.basicAuthPassword is not the configured basicAuthPassword"

    start_task.cancel()
