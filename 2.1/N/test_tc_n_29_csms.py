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
