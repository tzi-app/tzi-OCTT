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
