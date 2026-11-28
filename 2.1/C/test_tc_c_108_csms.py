"""
Test case name      Integrated Payment Terminal - VAT number validation
Test case Id        TC_C_108_CSMS
Use case Id(s)      C18
Requirement(s)      C18.FR.09, C18.FR.10

Requirement Details:
    C18.FR.09: CSMS validates given VAT number and responds with VatNumberValidationResponse with status =
               Accepted if validated and Rejected when invalid.
        Precondition: C18.FR.08
        Note: Optionally the company address can be returned in company field.
    C18.FR.10: CSMS SHALL use the same evseId in VatNumberValidationResponse.
        Precondition: If VatNumberValidationRequest received by CSMS contains an evseId
        Note: This can make it simpler for Charging Station to associate the data with the correct
              transaction.
System under test   CSMS

Description         To start/authorize a transaction from a payment terminal connected directly to the
                    Charging Station.

Purpose             To verify that the CSMS can validate VAT numbers correctly

Prerequisite(s)     - CSMS supports VAT number validation

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Valid VAT number with EVSE ID
1. The Test System sends a VatNumberValidationRequest with
    - vatNumber = <validVatNumber>
    - evseId = 1
2. The CSMS validates given VAT number and responds with VatNumberValidationResponse

Invalid VAT number with EVSE ID
3. The Test System sends a VatNumberValidationRequest with
    - vatNumber = <invalidVatNumber>
    - evseId = 1
4. The CSMS validates given VAT number and responds with VatNumberValidationResponse

Valid VAT number without EVSE ID
5. The Test System sends a VatNumberValidationRequest with
    - vatNumber = <validVatNumber>
    - evseId = <omitted>
6. The CSMS validates given VAT number and responds with VatNumberValidationResponse

Invalid VAT number without EVSE ID
7. The Test System sends a VatNumberValidationRequest with
    - vatNumber = <invalidVatNumber>
    - evseId = <omitted>
8. The CSMS validates given VAT number and responds with VatNumberValidationResponse

Tool validations
* Step 2:
    Message VatNumberValidationResponse
    - vatNumber must be <validVatNumber>
    - evseId must be 1
    - status must be Accepted
* Step 4:
    Message VatNumberValidationResponse
    - vatNumber must be <invalidVatNumber>
    - evseId must be 1
    - status must be Rejected
* Step 6:
    Message VatNumberValidationResponse
    - vatNumber must be <validVatNumber>
    - evseId must be <omitted>
    - status must be Accepted
* Step 8:
    Message VatNumberValidationResponse
    - vatNumber must be <invalidVatNumber>
    - evseId must be <omitted>
    - status must be Rejected

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
VALID_VAT_NUMBER = os.environ['VALID_VAT_NUMBER']
INVALID_VAT_NUMBER = os.environ['INVALID_VAT_NUMBER']


async def _validate_vat_number(cp, vat_number, evse_id, expected_status):
    response = await cp.call(call.VatNumberValidation(vat_number=vat_number, evse_id=evse_id))
    assert response.vat_number == vat_number, \
        f"Expected VatNumberValidationResponse.vatNumber {vat_number}, got {response.vat_number}"
    assert response.evse_id == evse_id, \
        f"Expected VatNumberValidationResponse.evseId {evse_id if evse_id is not None else '<omitted>'}, " \
        f"got {response.evse_id}"
    assert response.status == expected_status, \
        f"Expected VatNumberValidationResponse.status {expected_status} for {vat_number}, " \
        f"got {response.status}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_c_108(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Valid VAT number with EVSE ID
    # 1. The Test System sends a VatNumberValidationRequest with vatNumber <validVatNumber>,
    #    evseId 1
    # 2. The CSMS validates given VAT number and responds with VatNumberValidationResponse:
    #    vatNumber <validVatNumber>, evseId 1, status Accepted
    await _validate_vat_number(cp, VALID_VAT_NUMBER, 1, 'Accepted')

    # Invalid VAT number with EVSE ID
    # 3. The Test System sends a VatNumberValidationRequest with vatNumber <invalidVatNumber>,
    #    evseId 1
    # 4. The CSMS validates given VAT number and responds with VatNumberValidationResponse:
    #    vatNumber <invalidVatNumber>, evseId 1, status Rejected
    await _validate_vat_number(cp, INVALID_VAT_NUMBER, 1, 'Rejected')

    # Valid VAT number without EVSE ID
    # 5. The Test System sends a VatNumberValidationRequest with vatNumber <validVatNumber>,
    #    evseId <omitted>
    # 6. The CSMS validates given VAT number and responds with VatNumberValidationResponse:
    #    vatNumber <validVatNumber>, evseId <omitted>, status Accepted
    await _validate_vat_number(cp, VALID_VAT_NUMBER, None, 'Accepted')

    # Invalid VAT number without EVSE ID
    # 7. The Test System sends a VatNumberValidationRequest with vatNumber <invalidVatNumber>,
    #    evseId <omitted>
    # 8. The CSMS validates given VAT number and responds with VatNumberValidationResponse:
    #    vatNumber <invalidVatNumber>, evseId <omitted>, status Rejected
    await _validate_vat_number(cp, INVALID_VAT_NUMBER, None, 'Rejected')

    start_task.cancel()
