"""
Test case name      Authorization by GroupId - Invalid status with Local Authorization List
Test case Id        TC_C_43_CSMS
Use case Id(s)      C09
Requirement(s)      C09_FR_02, C09_FR_03

Requirement Details:
    C09.FR.02: IdTokens that are part of the same group for authorization purposes SHALL have a common group
               identifier in the optional groupIdToken element in IdTokenInfo
    C09.FR.03: An EV Driver with a different, valid IdToken, but with the same groupIdToken SHALL be
               authorized to stop the transaction.
        Precondition: When a transaction has been authorized/started with a certain IdToken.
System under test   CSMS

Description         This test case covers how a Charging Station can authorize an action for an EV Driver
                    based on GroupId information. This could for example be used if 2 people regularly use the
                    same EV: they can use their own IdToken (e.g. RFID card), and can deauthorize transactions
                    that were started with the other idToken (with the same GroupId).

Purpose             To verify if the CSMS is able to correctly handle the Authorization of idTokens with the
                    same GroupId which are located in the Local Authorization List according to the mechanism
                    as described in the OCPP specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        Two known valid idTokens with same GroupId are configured.

Reusable State(s)   state is EVConnectedPreSession

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    if transaction was already started
    - eventType Updated
    else
    - eventType Started
2. The CSMS responds with a TransactionEventResponse
3. Execute Reusable State EnergyTransferStarted
4. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
5. The CSMS responds with an AuthorizeResponse
6. The Test System sends a TransactionEventRequest with
    - triggerReason StopAuthorized
    - idToken.idToken <Configured valid_idtoken2_idtoken>
    - idToken.type <Configured valid_idtoken2_type>
    - eventType Updated
7. The CSMS responds with a TransactionEventResponse
8. Execute Reusable State EVConnectedPostSession
9. Execute Reusable State EVDisconnected

Tool validations
* Step 1:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 5:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 7:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

Post scenario validations:
    - N/a
"""
