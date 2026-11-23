"""
Test case name      Alert Event - HardWiredMonitor
Test case Id        TC_N_21_CSMS
Use case Id(s)      N07
Requirement(s)      N07.FR.03

Requirement Details:
    N07.FR.03: The CSMS SHALL respond with an empty NotifyEventResponse.
        Precondition: When the CSMS receives an NotifyEventRequest
System under test   CSMS

Description         Charging Station sends an NotifyEventRequest for a HardWiredMonitor.

Purpose             To test that the CSMS is able to handle a HardWiredMonitor.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Test System sends NotifyEventRequest message with
    - eventNotificationType = HardWiredMonitor
2. CSMS returns NotifyEventResponse message.

Tool validations
* Step 2:
    Message: NotifyEventResponse with empty body.

Post scenario validations:
    N/A
"""
