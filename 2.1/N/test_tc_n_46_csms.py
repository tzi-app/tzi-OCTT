"""
Test case name      Clear Customer Information - Update Local Authorization List
Test case Id        TC_N_46_CSMS
Use case Id(s)      N10
Requirement(s)      N10.FR.02, N10.FR.08, D01.FR.01, D01.FR.06, D01.FR.18,

Requirement Details:
    N10.FR.02: The CSMS SHALL update the Local Authorization List using the SendLocalListRequest (see D01 -
               Send Local Authorization List).
        Precondition: When the Customer referred to by the customer identifier is present in the Local
                      Authorization List of a Charging Station
        Note: To prevent problems with Local Authorization List versions.
    N10.FR.08: The CSMS SHALL include a reference to a customer by including either an idToken,
               customerCertificate or customerIdentifier in the CustomerInformationRequest.
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number
               (versionNumber) that the Charging Station MUST associate with the Local Authorization List
               after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique.
        Note: No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0.
        Note: In GetLocalListVersionResponse the versionNumber = 0 has a special meaning: No Local List
              installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a message to the Charging Station to clear (and retrieve) raw customer
                    information, for example to be compliant with local privacy laws. The Charging Station
                    notifies the CSMS by sending one or more reports.

Purpose             To verify if the CSMS updates the local authorization list when customer information,
                    which was present in the local authorization list, has been removed as described at the
                    OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        A local authorization list with <Configured valid_idtoken_idtoken> is configured.

Reusable State      N/a

Test Scenario
Manual action: Trigger CSMS to CustomerInformationRequest to both report and clear token <Configured
               valid_idtoken_idtoken> and <Configured valid_idtoken_type>

1. The CSMS sends a CustomerInformationRequest
2. The Test System responds with a CustomerInformationResponse
    with status Accepted
3. The Test System sends a NotifyCustomerInformationRequest
4. The CSMS responds with a NotifyCustomerInformationResponse .

Manual action: If not triggered automatically, trigger CSMS to send SendLocalListRequest
with version = <configured local list version> + 1
and updateType = Differential
and localAuthorizationList = [{idToken = {<Configured_valid_idtoken>, <Configured valid_idtoken_type>} }]

5. The CSMS sends a SendLocalListRequest
6 The Test System responds with a SendLocalListResponse with status Accepted

Tool validations
* Step 1:
    Message CustomerInformationRequest
    - report true AND
    - clear true AND
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
* Step 5:
    Message SendLocalListRequest
    - updateType Differential
    - versionNumber <configured local list version> + 1
    - localAuthorizationListp[0].idToken contains <configured_valid_idtoken_idtoken> and <configured
      valid_idtoken_type>
    - localAuthorizationList[0].idTokenInfo <omitted>

Post scenario validations:
    - All messages have been received
"""
