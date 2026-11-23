"""
State               Reserved
System under test   CSMS
Description         This state will simulate a reservation for a specified evse.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send a ReserveNowRequest for specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse With status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the Specified EVSE
   Message: StatusNotificationRequest
   with connectorStatus Reserved
   Message: NotifyEventRequest
   with trigger Delta
   actualValue "Reserved"
   component.name "Connector"
   variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1: Message: ReserveNowRequest
  - evseId must be <Specified evseId>
  - connectorType must be omitted
  - idToken.idToken <Configured valid_idtoken_idtoken>
  - idToken.type <Configured valid_idtoken_type>
Post condition      State is Reserved
"""
