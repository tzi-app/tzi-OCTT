"""
Test case name      Set Display Message - Specific transaction - Display message at StartTime
Test case Id        TC_O_27_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send the request with a startTime for a specific
                    transaction according to the DisplayMessage mechanism as described in the OCPP
                    specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a1

Reusable State      State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.state is <omitted>
    - message.startDateTime is <Configured startDateTime>
    - message.endDateTime is <omitted>
    - message.transactionId is <Generated transactionId from Before>

Post scenario validations:
    - N/a
"""
