"""
Test case name      Stop transaction options - Deauthorized - Invalid idToken
Test case Id        TC_E_16_CSMS
Use case Id(s)      E06(S3)
Requirement(s)      E06.FR.04, E01.FR.11, E01.FR.12

Requirement Details:
    E06.FR.04: See use case E05 - Start Transaction - Id not Accepted,
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a
                      TransactionEventResponse
    E01.FR.11: The CSMS SHALL verify the validity of the identifier in TransactionEventRequest.
        Precondition: E01.FR.10
    E01.FR.12: The CSMS SHALL send a TransactionEventResponse that includes in idTokenInfo an authorization
               status value and the groupIdToken if one exists for the idToken.
        Precondition: E01.FR.11
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the transaction gets deauthorized by the status from the idTokenInfo at a
                    TransactionEventResponse message and it has been configured to do so.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest With
    - triggerReason is Authorized
    - idToken.idToken <Configured invalid_idtoken_idtoken>
    - idToken.type <Configured invalid_idtoken_type>
    - eventType is Started
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest With
    - eventType Ended
    - triggerReason Deauthorized
    - transactionInfo.stoppedReason DeAuthorized
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Invalid or Unknown+

Post scenario validations:
    N/a
"""
