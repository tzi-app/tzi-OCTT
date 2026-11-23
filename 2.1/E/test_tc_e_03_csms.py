"""
Test case name      Local start transaction - Cable plugin first - Success
Test case Id        TC_E_03_CSMS
Use case Id(s)      E02
Requirement(s)      E02.FR.02

Requirement Details:
    E02.FR.02: The CSMS SHALL send a TransactionEventResponse that includes an authorization status value.
        Precondition: E02.FR.01
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR present a form
                    of identification.
                    Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that is able to start a
                    charging session when the
                    EV driver first connects the EV and EVSE, before authorization.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. Execute Reusable State Authorized
2. Execute Reusable State EnergyTransferStarted

Tool validations
N/a

Post scenario validations:
    N/a
"""
