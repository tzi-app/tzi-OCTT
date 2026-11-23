"""
Test case name      Clock-aligned Meter Values - Transaction ongoing
Test case Id        TC_J_02_CSMS
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
                    Values, when there is an ongoing transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted for <Configured evseId>

Test Scenario
1. The Test System notifies the CSMS about its measured Meter Values.
    Message: MeterValuesRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - sampledValue.context is Sample.Clock
    Message: NotifyEventRequest
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - trigger is Periodic
    - component.name is FiscalMetering
    Note(s):
    - This step will be executed every _<Configured clock-aligned Meter Values interval>
    - This step will be executed for evseId=0 and all configured idle EVSE.
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With
    - triggerReason is MeterValueClock
    - eventType is Updated
    - timestamp <The intervals between the timestamps of the received Meter Value messages equals the
      configured clock-aligned Meter Values interval>.
    - sampledValue.context is Sample.Clock
    Note(s):
    - This step will be executed every _<Configured clock-aligned Meter Values interval>
    - The Test System will end the testcase after the _<Configured transaction duration> is reached._
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
