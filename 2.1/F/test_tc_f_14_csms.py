"""
Test case name      Trigger message - TransactionEvent - All EVSE
Test case Id        TC_F_14_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a
                    TransactionEventRequest for all EVSE, using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System sends a TransactionEventRequest
    With evse.id omitted
    - triggerReason Trigger
    - transactionInfo.chargingState Charging
    - meterValue is present
    - meterValue[0].sampledValue.context Trigger
    Note(s):
    - This step will be executed for every EVSE.
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be TransactionEvent

Post scenario validations:
    N/a
"""
