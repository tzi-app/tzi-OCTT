"""
Test case name      Trigger Message
Test case Id        TC_054_CSMS
Feature profile     Remote Trigger
Document ref        Table 176, pages 149-150, Section 3.18.1

Description         The Central System triggers a message from the Charge Point.

Purpose             Check whether the Central System is able to trigger a message from the Charge Point.

Prerequisite(s)     The Central System supports the Remote Trigger feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
1.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = MeterValues
        - connectorId = <Configured ConnectorId>
2.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
3.  The Charge Point sends a MeterValues.req
4.  The Central System responds with a MeterValues.conf

5.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = Heartbeat
6.  The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
7.  The Charge Point sends a Heartbeat.req
8.  The Central System responds with a Heartbeat.conf

9.  The Central System sends a TriggerMessage.req with:
        - requestedMessage = StatusNotification
        - connectorId = <Configured ConnectorId>
10. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
11. The Charge Point sends a StatusNotification.req
12. The Central System responds with a StatusNotification.conf

13. The Central System sends a TriggerMessage.req with:
        - requestedMessage = DiagnosticsStatusNotification
14. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted
15. The Charge Point sends a DiagnosticsStatusNotification.req with:
        - status = Idle
16. The Central System responds with a DiagnosticsStatusNotification.conf

17. The Central System sends a TriggerMessage.req with:
        - requestedMessage = FirmwareStatusNotification
18. The Charge Point responds with a TriggerMessage.conf with:
        - status = Accepted OR NotImplemented
    [The following message will be sent if implemented.]
19. The Charge Point sends a FirmwareStatusNotification.req with:
        - status = Idle
20. The Central System responds with a FirmwareStatusNotification.conf

Tool validations
* Step 1:
    (Message: TriggerMessage.req)
    - requestedMessage should be MeterValues
    - connectorId should be <Configured ConnectorId>
* Step 2:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 5:
    (Message: TriggerMessage.req)
    - requestedMessage should be Heartbeat
* Step 6:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 9:
    (Message: TriggerMessage.req)
    - requestedMessage should be StatusNotification
    - connectorId should be <Configured ConnectorId>
* Step 10:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 13:
    (Message: TriggerMessage.req)
    - requestedMessage should be DiagnosticsStatusNotification
* Step 14:
    (Message: TriggerMessage.conf)
    - status is Accepted
* Step 15:
    (Message: DiagnosticsStatusNotification.req)
    - status is Idle
* Step 17:
    (Message: TriggerMessage.req)
    - requestedMessage should be FirmwareStatusNotification
* Step 18:
    (Message: TriggerMessage.conf)
    - status is Accepted OR NotImplemented
* Step 19:
    (Message: FirmwareStatusNotification.req)
    - status is Idle

Expected result(s)
    The Central System can request a message from a Charge Point and receive the requested message.
"""
