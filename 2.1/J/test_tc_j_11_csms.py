"""
Test case name      Sampled Meter Values - Signed
Test case Id        TC_J_11_CSMS
Use case Id(s)      J02
Requirement(s)      J02.FR.21

Requirement Details:
    J02.FR.21: The Charging Station SHALL retrieve signed meter values from components that support data
               signing and put them in the signedMeterValue field.
        Precondition: SampledDataSignReadings is true
System under test   CSMS

Description         The Charging Station samples the electrical meter or other sensor/transducer hardware to
                    provide information about its Meter Values. Depending on configuration settings, the
                    Charging Station will send Meter Values.

Purpose             To verify if the CSMS is able to handle a Charging Station sending sampled Meter Values,
                    when a transaction ends.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. Execute Reusable State EVDisconnected
    - The TransactionEventRequest containing eventType Ended contains the MeterValue field.
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured value at configured clock-aligned Tx ended Meter Values interval>.
    - sampledValue.context is Sample.Periodic AND the last one has Transaction.End
    - sampledValue.signedMeterValue is <Generated SignedMeterValueType>

Note(s):
- This step will be executed after the _<Configured transaction duration> is reached._
- This causes the transaction to stop.

Tool validations
N/a

Post scenario validations:
    N/a
"""
