"""
Test case name      Authorization by GroupId - Success with Local Authorization List
Test case Id        TC_C_40_CSMS
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

Memory State        Two valid idTokens with same GroupId are configured

Reusable State(s)   state is EVConnectedPreSession

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - triggerReason Authorized
    - idToken.idToken <Configured valid_idtoken_idtoken> (with a configured GroupId) which is configured in
      the local Authorization List
    - idToken.type <Configured valid_idtoken_type> (with a configured GroupId) which is configured in the
      local Authorization List
    If transaction was already started
    - eventType Updated
    else
    - eventType Started
2. The CSMS responds with a TransactionEventResponse
3. Execute Reusable State EnergyTransferStarted
5. The Test System sends a TransactionEventRequest with
    - triggerReason StopAuthorized
    - idToken.idToken <Configured valid_idtoken2_idtoken> (with same configured GroupId) which is configured
      in the local Authorization List>_
    - idToken.type <Configured valid_idtoken2_type>
    - eventType Updated
6. The CSMS responds with a TransactionEventResponse
7. Execute Reusable State EVConnectedPostSession
8. Execute Reusable State EVDisconnected

Tool validations
* Step 2:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>
* Step 6:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured groupIdToken>

Post scenario validations:
    - N/a
"""
