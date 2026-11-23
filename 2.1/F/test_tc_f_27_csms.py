"""
Test case name      Trigger message - NotImplemented
Test case Id        TC_F_27_CSMS
Use case Id(s)      F06
Requirement(s)      F06.FR.08

Requirement Details:
    F06.FR.08: The Charging Station SHALL respond with TriggerMessageResponse with status NotImplemented.
        Precondition: When the Charging Station receives a TriggerMessageRequest with a requestedMessage that
                      it has not implemented
System under test   CSMS

Description         The CSMS can request a Charging Station to send Charging Station-initiated messages. In
                    the request the CSMS indicates which message it wishes to receive.

Purpose             To verify if the CSMS is able to handle a Charging Station that does not support the
                    requested message value from a TriggerMessageRequest.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse with status NotImplemented

Tool validations
N/a

Post scenario validations:
    N/a
"""
