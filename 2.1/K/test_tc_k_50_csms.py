"""
Test case name      EMS Control - Reset / release external charging limit - Without ongoing transaction
Test case Id        TC_K_50_CSMS
Use case Id(s)      K13
Requirement(s)      N/a
System under test   CSMS

Description         A charging schedule or charging limit can be removed by an external system on the Charging
                    Station. An external control system sends a signal to release a previously imposed
                    charging limit to a Charging Station. The Charging Station notifies the CSMS about this.

Purpose             To verify if the CSMS is able to receive the notify from a charging station and respond
                    correctly as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a ClearedChargingLimitRequest with
    - chargingLimitSource EMS
2. The CSMS responds with a ClearedChargingLimitResponse

Tool validations
- N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_50(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The Test System sends a ClearedChargingLimitRequest with
    #    - chargingLimitSource EMS
    # 2. The CSMS responds with a ClearedChargingLimitResponse
    await cp.call(call.ClearedChargingLimit(charging_limit_source='EMS'))

    start_task.cancel()
