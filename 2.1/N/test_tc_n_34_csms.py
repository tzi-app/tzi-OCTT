"""
Test case name      Retrieve Log Information - Rejected
Test case Id        TC_N_34_CSMS
Use case Id(s)      N01
Requirement(s)      N/a
System under test   CSMS

Description         This test case covers the functionality of getting log information from a Charging
                    Station. The CSMS can request a Charging Station to upload a file with log information to
                    a given location (URL). The format of this log file is not prescribed. The Charging
                    Station successfully uploads a log file and gives information about the status of the
                    upload by sending status notifications to the CSMS.

Purpose             To verify if the CSMS is able to request a charging station to successfully upload a log
                    as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetLogRequest
2. The Test System responds with a GetLogResponse with status Rejected

Tool validations
N/a

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from diagnostics import request_log
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_34(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a GetLogRequest
    # 2. The Test System responds with a GetLogResponse with status Rejected
    await request_log(cp, 'DiagnosticsLog', status='Rejected')

    start_task.cancel()
