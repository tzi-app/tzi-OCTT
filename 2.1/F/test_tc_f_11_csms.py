"""
Test case name      Trigger message - MeterValues - Specific EVSE
Test case Id        TC_F_11_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01, F06.FR.02

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
    F06.FR.02: The CSMS MAY indicate to which EVSE this request applies.
        Precondition: F06.FR.01. For every such requested message.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a MeterValuesRequest
                    for a specific EVSE, using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System sends a MeterValuesRequest
    - With evseId <Configured evseId>
    - meterValue[0].sampledValue.context Trigger
4. The CSMS responds with a MeterValuesResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be MeterValues
    - evse.id must be <Configured evseId>

Post scenario validations:
    N/a
"""
