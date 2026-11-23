"""
Test case name      Authorization through authorization cache - Accepted
Test case Id        TC_C_08_CSMS
Use case Id(s)      C12
Requirement(s)      C12_FR_03

Requirement Details:
    C12.FR.03: The CSMS SHALL check the authorization status of the IdToken when processing this
               TransactionEventRequest.
        Precondition: C12.FR.02
System under test   CSMS

Description         This test case describes how the EV Driver is authorized to start a transaction while the
                    Charging Station uses Cached IdToken. This enables the EV Driver to Online start a
                    transaction by using the Authorization Cache in which the Charging Station can respond
                    faster, as no AuthorizeRequest is being sent.

Purpose             To verify if the CSMS is able to respond correctly when an idToken which has status
                    "Accepted" in the charging stations cache is presented according to the mechanism as
                    described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EVConnectedPreSession

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken <Valid id token configured in Authorization Cache>
    - eventType Updated
    Note(s):
    - TxStartPoint contains ParkingBayOccupancy
2. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted

Post scenario validations:
    - N/a
"""
