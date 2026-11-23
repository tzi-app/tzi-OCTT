"""
Test case name      Set Display Message - Success
Test case Id        TC_O_01_CSMS
Use case Id(s)      O01
Requirement(s)      O01_FR_04

Requirement Details:
    O01.FR.04: When a CSMS sends a message to a Charging Station that does not belong to a transaction, the
               field: transactionId in the message field SHALL be omitted.
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send the request according to the DisplayMessage
                    mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a SetDisplayMessageRequest.

1. The CSMS sends a SetDisplayMessageRequest with:
    - state <Configured display message state>
2. The Test System responds with a SetDisplayMessageResponse with:
    - status Accepted

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.id <Generated Id>
    - message.priority <Configured Priority>
    - message.message.format <Configured Format>
    - message.state <Configured State>

Post scenario validations:
    - N/a
"""
