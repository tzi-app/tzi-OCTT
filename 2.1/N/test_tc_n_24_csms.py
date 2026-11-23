"""
Test case name      Set Variable Monitoring - Periodic event
Test case Id        TC_N_24_CSMS
Use case Id(s)      N08
Requirement(s)      N08.FR.02

Requirement Details:
    N08.FR.02: The CSMS SHALL respond with an empty NotifyEventResponse.
        Precondition: When the CSMS receives an NotifyEventRequest
System under test   CSMS

Description         Charging Station sends a periodic NotifyEventRequest.

Purpose             To test that CSMS returns a NotifyEventResponse.
                    Note: this is identical to TC_N_21_CSMS, only with a periodic event.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Tester makes Test System send a NotifyEventRequest message.

1. Test System sends NotifyEventRequest message.
2. CSMS returns NotifyEventResponse message.

Note(s):
- Step 1 and 2 will be repeated n times

Tool validations
* Step 2:
    Message: NotifyEventResponse with empty body.

Post scenario validations:
    N/A
"""
