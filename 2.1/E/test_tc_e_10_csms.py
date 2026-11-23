"""
Test case name      Start transaction options - Authorized - Local
Test case Id        TC_E_10_CSMS
Use case Id(s)      E01(S3)
Requirement(s)      E01.FR.03

Requirement Details:
    E01.FR.03: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: Authorized AND The EV Driver is authorized AND No transaction has
                      started yet
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the EV and EVSE are connected.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest with:
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with:
    - eventType is Started
    - triggerReason is Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 4:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted

Post scenario validations:
    N/a
"""
