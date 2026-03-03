"""
Test case name      Get Variables - limit to maximum number of values
Test case Id        TC_B_08_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.05

Requirement Details:
    B06.FR.05: The CSMS SHALL NOT send more GetVariableData elements in a GetVariablesRequest than reported by the Charging Station via ItemsPerMessageGetVariables.
System under test   CSMS

Description         Do not request more variables than supported by MaxItemsPerMessageGetVariables.
Purpose             To test that CSMS does not request more variables than the Charging Station reported
                    to support in the variable MaxItemsPerMessageGetVariables.

Prerequisite(s)     N/a

Configuration State:
    Configure (using getVariablesRequest) Component.Variable.Instance
    DeviceDataCtrlr.ItemsPerMessage.GetVariables at value 4.

Test Scenario
1. Manually request CSMS for 5 variables:
   - DeviceDataCtrlr.ItemsPerMessage[ GetReport ]
   - DeviceDataCtrlr.ItemsPerMessage[ GetVariables ]
   - DeviceDataCtrlr.BytesPerMessage[ GetReport ]
   - DeviceDataCtrlr.BytesPerMessage[ GetVariables ]
   - AuthCtrlr.AuthorizeRemoteStart
2. OCTT responds with GetVariablesResponse(s)

Tool validations
* Step 1:
    Message: GetVariablesRequest for 4 variables and a GetVariablesRequest for 1 variable (in arbitrary order):
    for component.name = "DeviceDataCtrlr"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetReport"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetVariables"
    - variable.name = "BytesPerMessage" with variable.instance = "GetReport"
    - variable.name = "BytesPerMessage" with variable.instance = "GetVariables"
    and for component.name = "AuthCtrlr"
    - variable.name = "AuthorizeRemoteStart"

Post scenario validations:
    OCTT validates that not more than ItemsPerMessageGetVariables elements are requested
    in one GetVariablesRequest message by CSMS.
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from trigger import set_items_per_message, get_variables
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])

MAX_ITEMS_PER_MESSAGE = 4
# Each expected variable is (component.name, variable.name, variable.instance or None)
EXPECTED_VARIABLES = {
    ("DeviceDataCtrlr", "ItemsPerMessage", "GetReport"),
    ("DeviceDataCtrlr", "ItemsPerMessage", "GetVariables"),
    ("DeviceDataCtrlr", "BytesPerMessage", "GetReport"),
    ("DeviceDataCtrlr", "BytesPerMessage", "GetVariables"),
    ("AuthCtrlr", "AuthorizeRemoteStart", None),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_08(connection):
    """Get Variables - limit to max: CSMS must not exceed MaxItemsPerMessageGetVariables."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    cp._get_variables_values = {
        'DeviceDataCtrlr.ItemsPerMessage': '4',
        'DeviceDataCtrlr.BytesPerMessage': '4096',
        'AuthCtrlr.AuthorizeRemoteStart': 'true',
    }
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Set ItemsPerMessageGetVariables limit to 4
    await set_items_per_message(BASIC_AUTH_CP, get_variables=MAX_ITEMS_PER_MESSAGE)

    # Trigger CSMS to send GetVariablesRequest for 5 variables (should split into 4 + 1)
    trigger_task = asyncio.create_task(get_variables(BASIC_AUTH_CP, [
        {"component": {"name": "DeviceDataCtrlr"}, "variable": {"name": "ItemsPerMessage", "instance": "GetReport"}},
        {"component": {"name": "DeviceDataCtrlr"}, "variable": {"name": "ItemsPerMessage", "instance": "GetVariables"}},
        {"component": {"name": "DeviceDataCtrlr"}, "variable": {"name": "BytesPerMessage", "instance": "GetReport"}},
        {"component": {"name": "DeviceDataCtrlr"}, "variable": {"name": "BytesPerMessage", "instance": "GetVariables"}},
        {"component": {"name": "AuthCtrlr"}, "variable": {"name": "AuthorizeRemoteStart"}},
    ]))

    # Wait for first GetVariablesRequest
    await asyncio.wait_for(
        cp._received_get_variables.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )

    first_batch = cp._get_variables_data
    assert first_batch is not None

    batch_sizes = [len(first_batch)]
    requested_vars = set()
    for item in first_batch:
        comp_name = item.get('component', {}).get('name', '')
        var_name = item.get('variable', {}).get('name', '')
        var_instance = item.get('variable', {}).get('instance', None)
        requested_vars.add((comp_name, var_name, var_instance))

    # TC_B_08 requires two GetVariablesRequest messages split into 4 and 1 items (order arbitrary).
    cp._received_get_variables.clear()
    await asyncio.wait_for(
        cp._received_get_variables.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    second_batch = cp._get_variables_data
    assert second_batch is not None
    batch_sizes.append(len(second_batch))
    for item in second_batch:
        comp_name = item.get('component', {}).get('name', '')
        var_name = item.get('variable', {}).get('name', '')
        var_instance = item.get('variable', {}).get('instance', None)
        requested_vars.add((comp_name, var_name, var_instance))

    assert sorted(batch_sizes) == [1, 4], \
        f"Expected GetVariablesRequest split sizes [4,1] in arbitrary order, got {batch_sizes}"

    for size in batch_sizes:
        assert size <= MAX_ITEMS_PER_MESSAGE, \
            f"CSMS requested {size} variables in one message, max allowed is {MAX_ITEMS_PER_MESSAGE}"

    assert requested_vars == EXPECTED_VARIABLES, \
        f"Unexpected requested variables: {requested_vars}, expected: {EXPECTED_VARIABLES}"

    logging.info(f"Validated GetVariablesRequest split sizes {batch_sizes} and variables {sorted(EXPECTED_VARIABLES)}")

    await trigger_task
    start_task.cancel()
