"""
Test case name      Get Customer Information - Not Accepted
Test case Id        TC_N_29_CSMS
Use case Id(s)      N09
Requirement(s)      N09.FR.01, N09.FR.04

Requirement Details:
    N09.FR.01: The report flag in the CustomerInformationRequest SHALL be set to true.
        Precondition: When the CSMS wants to retrieve CustomerInformation from the Charging Station.
    N09.FR.04: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to retrieve IdToken customer information,
                    but the Charging Station rejects the request.

Purpose             To verify if the CSMS sends the request correctly as described at the OCPP specification,
                    and can handle the Charging Station rejecting the request.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a CustomerInformationRequest
2. The Test System responds with a CustomerInformationResponse with status Rejected

Tool validations
* Step 1:
    Message CustomerInformationRequest
    - report true
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from diagnostics import request_customer_information, validate_customer_information
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = {'idToken': os.environ['VALID_ID_TOKEN'], 'type': os.environ['VALID_ID_TOKEN_TYPE']}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_29(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a CustomerInformationRequest
    # 2. The Test System responds with a CustomerInformationResponse with status Rejected
    request = await request_customer_information(
        cp, report=True, clear=False, id_token=VALID_ID_TOKEN, status='Rejected')
    # report true, idToken.idToken <Configured valid_idtoken_idtoken>, idToken.type <Configured
    # valid_idtoken_type>
    validate_customer_information(request, report=True, id_token=VALID_ID_TOKEN)

    start_task.cancel()
