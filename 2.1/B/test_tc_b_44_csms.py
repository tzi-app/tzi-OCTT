"""
Test case name      Set new NetworkConnectionProfile - Failed
Test case Id        TC_B_44_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.03

Requirement Details:
    B09.FR.03: The Charging Station SHALL respond by sending a SetNetworkProfileResponse message, with status
               Failed
        Precondition: If setting a valid NetworkConnectionProfile in a SetNetworkProfileRequest fails.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify if the CSMS is able to handle a Charging Station responding with status Failed,
                    when setting a new network connection profile at one of the by the Charging Station
                    defined configuration slots.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse
    - With status Failed

Tool validations
N/a

Post scenario validations:
    - N/a
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
CONFIGURED_SECURITY_PROFILE = int(os.environ['CONFIGURED_SECURITY_PROFILE'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_44(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a SetNetworkProfileRequest
    # 2. The Test System responds with a SetNetworkProfileResponse With status Failed
    cp.set_response('SetNetworkProfile', status='Failed')
    await cp.wait_for_request(
        'SetNetworkProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'SetNetworkProfile', {
            'configurationSlot': CONFIGURED_CONFIGURATION_SLOT,
            'connectionData': {
                'messageTimeout': CONFIGURED_MESSAGE_TIMEOUT,
                'ocppCsmsUrl': CONFIGURED_OCPP_CSMS_URL,
                'ocppInterface': CONFIGURED_OCPP_INTERFACE,
                'ocppTransport': 'JSON',
                'ocppVersion': 'OCPP20',
                'securityProfile': CONFIGURED_SECURITY_PROFILE,
            },
        }))

    start_task.cancel()
