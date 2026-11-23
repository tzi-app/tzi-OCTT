"""
Test case name      Set Display Message - Replace DisplayMessage
Test case Id        TC_O_12_CSMS
Use case Id(s)      O06
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can replace a DisplayMessage that is previously
                    configured in a Charging Station. Replace the message content, but also all the given
                    parameters with the new one.

Purpose             To verify if the CSMS is able to request to replace a display message according to the
                    DisplayMessage mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        A display message is configured.

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to sent a display message with the same id as already configured one

1. The CSMS sends a SetDisplayMessageRequest with:
    - message.id <Configured_Id>
    - message.priority <Configured Priority>
2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations
* Step 2:
    Message SetDisplayMessageRequest
    - message.id <Configured_Id>
    - message.priority <Configured Priority>

Post scenario validations:
    - N/a
"""
