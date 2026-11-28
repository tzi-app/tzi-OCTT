"""
Test case name      Get Customer Information - Accepted + data
Test case Id        TC_N_27_CSMS
Use case Id(s)      N09
Requirement(s)      N09.FR.01, N09.FR.04

Requirement Details:
    N09.FR.01: The report flag in the CustomerInformationRequest SHALL be set to true.
        Precondition: When the CSMS wants to retrieve CustomerInformation from the Charging Station.
    N09.FR.04: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to retrieve IdToken customer information,
                    for example to be compliant with local privacy laws. The Charging Station notifies the
                    CSMS by sending one or more reports.

Purpose             To verify if the CSMS sends the request correctly and responds on the notifies as
                    described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a CustomerInformationRequest
2. The Test System responds with a CustomerInformationResponse with status Accepted
3. The Test System sends a NotifyCustomerInformationRequest
4. The CSMS responds with a NotifyCustomerInformationResponse.

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
async def test_tc_n_27(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # 1. The CSMS sends a CustomerInformationRequest
    # 2. The Test System responds with a CustomerInformationResponse with status Accepted
    request = await request_customer_information(cp, report=True, clear=False, id_token=VALID_ID_TOKEN)
    # report true, idToken.idToken <Configured valid_idtoken_idtoken>, idToken.type <Configured
    # valid_idtoken_type>
    validate_customer_information(request, report=True, id_token=VALID_ID_TOKEN)

    # 3. The Test System sends a NotifyCustomerInformationRequest: the data that the Test System
    #    has about the customer
    # 4. The CSMS responds with a NotifyCustomerInformationResponse.
    await cp.send_notify_customer_information(
        data=f"idToken {VALID_ID_TOKEN['idToken']}: 1 authorization cache entry, 2 transactions",
        seq_no=0, request_id=request.request_id)

    start_task.cancel()
