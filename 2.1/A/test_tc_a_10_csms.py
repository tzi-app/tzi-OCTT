"""
Test case name      Update Charging Station Password for HTTP Basic Authentication - Rejected
Test case Id        TC_A_10_CSMS
Use case Id(s)      A01
Requirement(s)      A01.FR.02, A01.FR.04, A01.FR.05

Requirement Details:
    A01.FR.02: To set a Charging Station’s basic authorization password via OCPP, the CSMS SHALL send the
               Charging Station a SetVariablesRequest message with the BasicAuthPassword Configuration
               Variable.
    A01.FR.04: The CSMS SHALL assume that the Charging Station has NOT changed the password. Therefore the
               CSMS SHALL keep accepting the old credentials.
        Precondition: A01.FR.02 AND The Charging Station responds to this SetVariablesRequest with a
                      SetVariablesResponse with status other than Accepted
    A01.FR.05: While the CSMS SHALL still accepts a connection from the Charging Station, it MAY restrict the
               functionality that the Charging Station can use. The CSMS can use the BootNotification state:
               Pending for this. During the Pending state, the CSMS can for example retry to update the
               credentials.
        Precondition: A01.FR.04
System under test   CSMS

Description         This test case defines how to use the BasicAuthPassword, the password used to authenticate
                    Charging Stations in security profile 1 (Basic Authentication) and security profile 2 (TLS
                    with Basic Authentication)

Purpose             To verify if the CSMS keeps accepting the old credentials and keeps communication when the
                    new BasicAuthPassword is rejected as described at the OCPP specification.

Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetVariablesRequest with:
    setVariableData[1]:
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"
    - attributeValue = "<NewPassword>"
2. The Test System responds with a SetVariablesResponse with status Rejected
3. The Test System sends a HTTP upgrade request with an Authorization header, containing a username/password
   combination (with the old BasicAuthPassword).
    Note(s):
    - The Authorization header is formatted as follows:
      AUTHORIZATION: Basic <Base64 encoded(<Configured ChargingStationId>:<OLD Configured BasicAuthPassword>)>
4. The CSMS validates the username/password combination AND upgrades the connection to a (secured) WebSocket
   connection.
5. The Test System sends a BootNotificationRequest
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
8. The CSMS responds accordingly.

Tool validations
* Step 1:
    Message: SetVariableRequest
    - variable.name = "BasicAuthPassword"
    - component.name = "SecurityCtrlr"
* Step 6:
    Message: BootNotificationResponse
    - status must be Accepted

Post scenario validations:
    N/a
"""
