"""
Test case name      Clock-aligned Meter Values - EventType Ended
Test case Id        TC_J_03_CSMS
Use case Id(s)      J01
Requirement(s)      J01.FR.18

Requirement Details:
    J01.FR.18: CSMS SHALL respond with MeterValuesResponse.
        Precondition: When CSMS receives a MeterValuesRequest
        Note: Failing to respond with MeterValuesResponse might cause the Charging Station to try the same
              message again.
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending clock-aligned Meter
                    Values, when a transaction ends.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. Execute Reusable State EVDisconnected
    - The TransactionEventRequest containing eventType Ended contains the MeterValue field.
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured value at configured clock-aligned Tx ended Meter Values interval>.
    - sampledValue.context is Sample.Clock AND the last one has Transaction.End

Note(s):
- This step will be executed after the _<Configured transaction duration> is reached._
- This causes the transaction to stop.

Tool validations
N/a

Post scenario validations:
    N/a
"""
