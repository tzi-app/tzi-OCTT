"""
Test case name      Get Base Report - ConfigurationInventory
Test case Id        TC_B_12_CSMS
Use case Id(s)      B07
Requirement(s)      B07.FR.07

Requirement Details:
    B07.FR.07: B07.FR.01 AND When reportBase is ConfigurationInventory Then the Charging Station SHALL respond with a NotifyReportRequest to report on all component-variables that can be set by the operator including their VariableCharacteristics.
        Precondition: B07.FR.01 AND When reportBase is ConfigurationInventory
System under test   CSMS

Description         CSMS requests a ConfigurationInventory base report.
Purpose             To test that CSMS supports the ConfigurationInventory base report.

Prerequisite(s)     N/a

Test Scenario
1. Manually instruct CSMS to retrieve a ConfigurationInventory report.
   CSMS sends a GetBaseReportRequest with:
   - requestId has integer value >= 0
   - reportBase = ConfigurationInventory
2. OCTT responds with GetBaseReportResponse

Post scenario validations:
    CSMS receives all NotifyReportRequest messages for this requestId and is able to show
    the result of configuration inventory.
"""

import asyncio
import pytest
import os
import logging
from ocpp.v201.enums import RegistrationStatusEnumType, ConnectorStatusEnumType

from tzi_charge_point import TziChargePoint
from trigger import get_base_report
from utils import get_basic_auth_headers

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection", [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_12(connection):
    """Get Base Report - ConfigurationInventory: CSMS requests configuration inventory."""
    cp = TziChargePoint(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Boot to establish session
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatusEnumType.accepted

    await cp.send_status_notification(1, ConnectorStatusEnumType.available)

    # Trigger CSMS to send GetBaseReportRequest with ConfigurationInventory
    trigger_task = asyncio.create_task(
        get_base_report(BASIC_AUTH_CP, "ConfigurationInventory")
    )

    # Wait for the CS to receive the GetBaseReportRequest
    await asyncio.wait_for(
        cp._received_get_base_report.wait(),
        timeout=CSMS_ACTION_TIMEOUT,
    )
    await trigger_task

    # Validate the GetBaseReportRequest content
    assert cp._get_base_report_data is not None
    request_id = cp._get_base_report_data['request_id']
    report_base = cp._get_base_report_data['report_base']

    assert isinstance(request_id, int) and request_id >= 0, \
        f"requestId must be integer >= 0, got: {request_id}"
    assert report_base == 'ConfigurationInventory', \
        f"Expected ConfigurationInventory reportBase, got: {report_base}"

    logging.info(f"GetBaseReportRequest validated: requestId={request_id}, reportBase={report_base}")

    # Send NotifyReportRequest with sample configuration data
    report_data = [{
        'component': {'name': 'OCPPCommCtrlr'},
        'variable': {'name': 'OfflineThreshold'},
        'variable_attribute': [{
            'type': 'Actual',
            'value': '60',
            'mutability': 'ReadWrite',
        }],
        'variable_characteristics': {
            'data_type': 'integer',
            'supports_monitoring': True,
        },
    }]

    await cp.send_notify_report(
        request_id=request_id,
        seq_no=0,
        report_data=report_data,
        tbc=False,
    )

    start_task.cancel()
