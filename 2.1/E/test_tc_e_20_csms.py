"""
Test case name      Stop transaction options - EVDisconnected - EV side (able to charge IEC 61851-1 EV)
Test case Id        TC_E_20_CSMS
Use case Id(s)      E06(S2), E10
Requirement(s)      E06.FR.02

Requirement Details:
    E06.FR.02: The Charging Station SHALL stop the transaction and send a TransactionEventRequest (eventType =
               Ended) to the CSMS.
        Precondition: TxStopPoint contains: EVConnected AND Connection between Charging Station and EV is
                      lost.
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the stop options.

Purpose             To verify if the CSMS is able to handle a Charging Station that stops a transaction when
                    the EV and EVSE are disconnected at the EV side.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferSuspended

Test Scenario
1. Execute Reusable State EVDisconnected

Tool validations
N/a

Post scenario validations:
    N/a
"""
