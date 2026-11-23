"""
Test case name      Connector status Notification - Lock Failure
Test case Id        TC_G_20_CSMS
Use case Id(s)      G05
Requirement(s)      G05.FR.03

Requirement Details:
    G05.FR.03: The CSMS SHALL respond with a NotifyEventResponse.
        Precondition: G05.FR.02
System under test   CSMS

Description         This test case describes how the EV Driver is prevented from starting a charge session at
                    the Charging Station while the Connector is not locked properly.

Purpose             To verify if the CSMS responds on a notifyeventrequest as described at the OCPP
                    specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The Test System sends a NotifyEventRequest with
    - eventData.trigger Delta
    - eventData.component.name "ConnectorPlugRetentionLock"
    - eventData.variable.name "Problem"
    - eventData.actualValue "true"
2. The CSMS responds with a NotifyEventResponse

Tool validations
N/a

Post scenario validations:
    - N/a
"""
