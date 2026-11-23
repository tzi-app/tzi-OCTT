"""
Test case name      Get Customer Information - Accepted + no data
Test case Id        TC_N_28_CSMS
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
