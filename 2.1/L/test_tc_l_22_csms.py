"""
Test case name      Unpublish Firmware - NoFirmware
Test case Id        TC_L_22_CSMS
Use case Id(s)      L04
Requirement(s)      N/a
System under test   CSMS

Description         Stop serving a firmware update to connected Charging Stations.

Purpose             To verify if the CSMS is able to unpublish a firmware on the local controller as described
                    at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a UnpublishFirmwareRequest
2. The Test System responds with a UnpublishFirmwareResponse with status NoFirmware

Tool validations
-N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from firmware import checksum
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_l_22(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a UnpublishFirmwareRequest
    # 2. The Test System responds with a UnpublishFirmwareResponse with status NoFirmware
    cp.set_response('UnpublishFirmware', status='NoFirmware')
    await cp.wait_for_request(
        'UnpublishFirmware',
        manual_action=send_call(BASIC_AUTH_CP, 'UnpublishFirmware', {'checksum': checksum()}))

    start_task.cancel()
