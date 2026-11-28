"""
Test case name      Clear Customer Information - Clear and report - customerIdentifier
Test case Id        TC_N_62_CSMS
Use case Id(s)      N10
Requirement(s)      N10.FR.08

Requirement Details:
    N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to clear (and retrieve) raw customer
                    information, for example to be compliant with local privacy laws. The Charging Station
                    notifies the CSMS by sending one or more reports.

Purpose             To verify if the CSMS sends the request correctly and responds to the notifications as
                    described in the OCPP specification.

Prerequisite(s)     The CSMS supports retrieving / deleting CustomerInformation - CustomerIdentifier

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a CustomerInformationRequest
2. The Test System responds with a CustomerInformationResponse with status Accepted
3. The Test System sends a NotifyCustomerInformationRequest
4. The CSMS responds with a NotifyCustomerInformationResponse

Tool validations
* Step 1:
    Message CustomerInformationRequest
    - report true
    - clear true
    - customerIdentifier "OpenChargeAlliance"
    - idToken is omitted
    - customerCertificate is omitted

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


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_62(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: The CSMS supports retrieving / deleting CustomerInformation -
    # CustomerIdentifier
    # 1. The CSMS sends a CustomerInformationRequest
    # 2. The Test System responds with a CustomerInformationResponse with status Accepted
    request = await request_customer_information(
        cp, report=True, clear=True, customer_identifier='OpenChargeAlliance')
    validate_customer_information(request, report=True, clear=True)
    assert request.customer_identifier == 'OpenChargeAlliance', \
        f"Expected CustomerInformationRequest.customerIdentifier \"OpenChargeAlliance\", " \
        f"got {request.customer_identifier}"
    assert request.id_token is None, \
        f"CustomerInformationRequest.idToken must be omitted, got {request.id_token}"
    assert request.customer_certificate is None, \
        f"CustomerInformationRequest.customerCertificate must be omitted, got {request.customer_certificate}"

    # 3. The Test System sends a NotifyCustomerInformationRequest
    # 4. The CSMS responds with a NotifyCustomerInformationResponse
    await cp.send_notify_customer_information(
        data='Customer OpenChargeAlliance: 1 authorization cache entry', seq_no=0,
        request_id=request.request_id)

    start_task.cancel()
