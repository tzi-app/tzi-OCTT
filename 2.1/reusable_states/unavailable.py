"""
State               Unavailable
System under test   CSMS
Description         This state will simulate that Charging Station / EVSEs / connectors are set to
                    AvailabilityState Unavailable.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Request the CSMS to change the availability of the specified components to Inoperative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors belonging to the specified EVSE
   (and optionally also from the EVSE itself).
   Message: StatusNotificationRequest
   - connectorStatus Unavailable
   Message: NotifyEventRequest
   - trigger Delta
   - actualValue "Unavailable"
   - component.name "ChargingStation" / EVSE / Connector
   - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1: Message ChangeAvailabilityRequest
  - operationalStatus Inoperative
  - evse <Specified evseId>
  - connectorId omitted
Post condition      State is Unavailable
"""
