"""
Test case name      Local start transaction - EV not ready
Test case Id        TC_E_38_CSMS
Use case Id(s)      E03
Requirement(s)      N/a
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR present a form
                    of identification. Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that reports an EV is not ready
                    to start the energy transfer (yet).

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is Authorized

Test Scenario
1. Execute Reusable State EVConnectedPreSession
2. The Test System sends a TransactionEventRequest With
    - triggerReason is ChargingStateChanged
    - transactionInfo.chargingState is SuspendedEV
    - eventType is Updated
3. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
