"""
State               EVConnectedPreSession
System under test   CSMS
Description         This state will simulate that the EV and EVSE of the simulated Charging Station are
                    connected.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System notifies the CSMS about the status change of the connector
   Message: StatusNotificationRequest
   - connectorStatus is Occupied
   Message: NotifyEventRequest
   - trigger is Delta
   - actualValue is Occupied
   - component.name is Connector
   - variable.name is AvailabilityState
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With triggerReason is CablePluggedIn
   transactionInfo.chargingState is EVConnected
   evse.id <Configured evseId>
   evse.connectorId <Configured connectorId>

If State is Authorized then
    eventType is Updated
else
    eventType is Started

4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVConnectedPreSession
"""
