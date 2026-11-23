"""
Test case name      Cold Boot Charging Station - Pending/Rejected - SecurityError
Test case Id        TC_B_30_CSMS
Use case Id(s)      B02/B03
Requirement(s)      B02.FR.09, B03.FR.07

Requirement Details:
    B02.FR.09: The CSMS SHALL respond with RPC Framework: CALLERROR: SecurityError.
        Precondition: The Charging Station has received a BootNotificationResponse with status Pending AND the
                      Charging Station sends a RPC Framework: CALL message that is NOT a
                      BootNotificationRequest or a message triggered by one of the following messages:
                      TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.
        Note: The Charging Station is not allowed to initiate sending other messages before being accepted.
    B03.FR.07: CSMS SHALL respond with RPC Framework: CALLERROR: SecurityError.
        Precondition: B03.FR.03 AND Charging Station sends a message that is not a BootNotificationRequest
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages. The CSMS may respond to the
                    BootNotificationRequest with status Pending or Rejected. During this state, the Charging
                    Station is not allowed to send RPC Framework: CALL message that is NOT a
                    BootNotificationRequest or in case of status Pending, a message triggered by one of the
                    following messages: TriggerMessageRequest, GetBaseReportRequest, GetReportRequest.

Purpose             To verify whether the CSMS is able to handle unauthorized messages from the Charging
                    Station by responding with a SecurityError.

Prerequisite(s)     The CSMS is configured to first respond to a BootNotificationRequest with status Pending
                    or Rejected.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a BootNotificationRequest with:
    - reason PowerUp
    - chargingStation.model <Configured model>
    - chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse
3. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest with:
    - connectorStatus Available
    Message: NotifyEventRequest with:
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
4. The CSMS responds with RPC Framework: CALLERROR: SecurityError.

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Pending OR Rejected

Post scenario validations:
    N/a
"""
