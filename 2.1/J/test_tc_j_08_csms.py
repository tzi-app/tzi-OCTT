"""
Test case name      Sampled Meter Values - Context Transaction.Begin - EVSE not known
Test case Id        TC_J_08_CSMS
Use case Id(s)      J02
Requirement(s)      J02.FR.19

Requirement Details:
    J02.FR.19: CSMS SHALL respond with TransactionEventResponse.
        Precondition: When CSMS receives a TransactionEventRequest
        Note: Failing to respond with TransactionEventResponse might cause the Charging Station to try the
              same message again.
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending start sampled Meter
                    Values, when a transaction starts.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Authorized
2. Execute Reusable State EVConnectedPreSession
    - The TransactionEventRequest contains the MeterValue field.
    - sampledValue.context is Transaction.Begin
3. Execute Reusable State EnergyTransferStarted

Tool validations
N/a

Post scenario validations:
    N/a
"""
