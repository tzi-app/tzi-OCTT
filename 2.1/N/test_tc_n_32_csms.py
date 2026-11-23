"""
Test case name      Clear Customer Information - Clear and no report
Test case Id        TC_N_32_CSMS
Use case Id(s)      N10
Requirement(s)      N10.FR.08

Requirement Details:
    N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to clear IdToken customer information,
                    for example to be compliant with local privacy laws.

Purpose             To verify if the CSMS sends the request correctly.

Prerequisite(s)     n/a

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
    - report false
    - clear true
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

Post scenario validations:
    - N/a
"""
