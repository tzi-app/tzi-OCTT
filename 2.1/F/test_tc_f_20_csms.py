"""
Test case name      Trigger message - Heartbeat
Test case Id        TC_F_20_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.01

Requirement Details:
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to trigger the Charging Station to send a HeartbeatRequest,
                    using a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status Accepted
3. The Test System sends a HeartbeatRequest
4. The CSMS responds with a HeartbeatResponse

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage must be Heartbeat

Post scenario validations:
    N/a
"""
