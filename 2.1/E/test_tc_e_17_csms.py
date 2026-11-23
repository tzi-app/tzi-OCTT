"""
Test case name      Stop transaction options - Deauthorized - EV side disconnect
Test case Id        TC_E_17_CSMS
Use case Id(s)      E06(S3)
Requirement(s)      E06.FR.04

Requirement Details:
    E06.FR.04: See use case E05 - Start Transaction - Id not Accepted,
        Precondition: TxStopPoint contains: Authorized AND CSMS returns a non-valid idTokenInfo in a
                      TransactionEventResponse
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the transaction gets deauthorized by a connection loss from the EV side and it has been
                    configured to do so.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferSuspended

Test Scenario
1. The Test System sends a TransactionEventRequest
    - triggerReason must be EVCommunicationLost
    - transactionInfo.chargingState must be Idle
    - transactionInfo.stoppedReason must be EVDisconnected
    - eventType must be Ended
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
