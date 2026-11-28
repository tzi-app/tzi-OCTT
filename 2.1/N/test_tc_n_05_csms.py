"""
Test case name      Set Monitoring Base - success
Test case Id        TC_N_05_CSMS
Use case Id(s)      N03
Requirement(s)      N03.FR.03, N03.FR.04, N03.FR.05

Requirement Details:
    N03.FR.03: Then the Charging Station SHALL activate all preconfigured monitoring whilst leaving all
               installed custom monitors (including changed preconfigured monitors) intact.
        Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with
                      monitoringBase All
    N03.FR.04: Then the Charging Station SHALL delete all custom monitors (including overruled pre-configured
               monitors) and activate the pre-configured monitors of the Charging Station.
        Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with
                      monitoringBase FactoryDefault
    N03.FR.05: Then the Charging Station SHALL clear all custom and disable all pre-configured monitors. Only
               hard-wired monitors remain active.
        Precondition: N03.FR.01 AND When the Charging Station received a setMonitoringBaseRequest with
                      monitoringBase HardWiredOnly
System under test   CSMS

Description         CSMS sends a SetMonitoringBaseRequest for All, FactoryDefault and HardWiredOnly.

Purpose             To test that CSMS supports all three monitoring base types.

Prerequisite(s)     CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Instruct CSMS to set a monitoring base of _All._

1. CSMS sends SetMonitoringBaseRequest
2. Test System responds with: SetMonitoringBaseResponse

Manual Action: Instruct CSMS to set a monitoring base of _FactoryDefault._

3. Test System sends SetMonitoringBaseRequest
4. Test System responds with: SetMonitoringBaseResponse

Manual Action: Instruct CSMS to set a monitoring base of _HardWiredOnly._

5. Test System sends SetMonitoringBaseRequest
6. The Test System responds with: SetMonitoringBaseResponse

Tool validations
* Step 1
    Message: SetMonitoringBaseRequest
    - monitoringBase = All
* Step 3
    Message: SetMonitoringBaseRequest
    - monitoringBase = FactoryDefault
* Step 6
    Message: SetMonitoringBaseRequest
    - monitoringBase = HardWiredOnly

Post scenario validations:
    N/A

Remarks
Transcribed as printed: steps 3 and 5 stand in the CSMS column of the scenario table but read "Test System
                        sends", and the third tool validation is labelled "Step 6".
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from monitoring import MONITORING_VARIABLES
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_05(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: Instruct CSMS to set a monitoring base of All.
    # 1. CSMS sends SetMonitoringBaseRequest
    # 2. Test System responds with: SetMonitoringBaseResponse
    # Manual Action: Instruct CSMS to set a monitoring base of FactoryDefault.
    # 3. CSMS sends SetMonitoringBaseRequest
    # 4. Test System responds with: SetMonitoringBaseResponse
    # Manual Action: Instruct CSMS to set a monitoring base of HardWiredOnly.
    # 5. CSMS sends SetMonitoringBaseRequest
    # 6. The Test System responds with: SetMonitoringBaseResponse
    for monitoring_base in ('All', 'FactoryDefault', 'HardWiredOnly'):
        request = await cp.wait_for_request(
            'SetMonitoringBase',
            manual_action=send_call(BASIC_AUTH_CP, 'SetMonitoringBase',
                                    {'monitoringBase': monitoring_base}))
        assert request.monitoring_base == monitoring_base, \
            f"Expected SetMonitoringBaseRequest.monitoringBase {monitoring_base}, " \
            f"got {request.monitoring_base}"

    start_task.cancel()
