"""
Test case name      Clear Customer Information - Clear and report - customerCertificate
Test case Id        TC_N_63_CSMS
Use case Id(s)      N10
Requirement(s)      N10.FR.08

Requirement Details:
    N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to clear (and retrieve) a customer
                    certificate, for example to be compliant with local privacy laws. The Charging Station
                    notifies the CSMS by sending one or more reports.

Purpose             To verify if the CSMS sends the request correctly and responds to the notifications as
                    described in the OCPP specification.

Prerequisite(s)     The CSMS supports retrieving / deleting CustomerInformation - CustomerCertificate

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a CustomerInformationRequest with specific hash data <customer certificate hash data>.
2. The Test System responds with a CustomerInformationResponse with status Accepted
3. The Test System sends a NotifyCustomerInformationRequest
4. The CSMS responds with a NotifyCustomerInformationResponse

Tool validations
* Step 1:
    Message CustomerInformationRequest
    - report true
    - clear true
    - customerCertificate contains <customer certificate hash data>

Post scenario validations:
    - N/a
"""
