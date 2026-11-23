"""
Test case name      Set Display Message - NotSupportedMessageFormat
Test case Id        TC_O_19_CSMS
Use case Id(s)      O01
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send a display message with a specific MessageFormat, on
                    which the Charging station responds not supported, according to the DisplayMessage
                    mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status NotSupportedMessageFormat

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.id <Generated Id>

Post scenario validations:
    - N/a
"""
