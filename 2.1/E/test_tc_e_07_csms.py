"""
Test case name      Stop transaction options - PowerPathClosed - Local stop
Test case Id        TC_E_07_CSMS
Use case Id(s)      E06(S5)
Requirement(s)      E06.FR.06

Requirement Details:
    E06.FR.06: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: PowerPathClosed AND ( Connection between Charging Station and EV
                      is lost OR Authorization has ended or idToken is deauthorized )
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    it is locally stopped by an EV driver.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest
    With triggerReason is StopAuthorized
    transactionInfo.stoppedReason is Local
    eventType is Ended
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
