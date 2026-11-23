"""
Test case name      Stop transaction options - ParkingBayUnoccupied
Test case Id        TC_E_19_CSMS
Use case Id(s)      E06(S1)
Requirement(s)      E06.FR.01

Requirement Details:
    E06.FR.01: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: ParkingBayOccupancy AND Parking Bay Detector no longer detects the
                      "EV"
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the EV left the parking bay.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVDisconnected

Test Scenario
1. The Test System sends a TransactionEventRequest With
    - triggerReason is EVDeparted
    - transactionInfo.stoppedReason is Local
    - eventType is Ended
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
