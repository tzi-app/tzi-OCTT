"""
State               EVDisconnected
System under test   CSMS
Description         This state will simulate that the EV and EVSE of the simulated Charging Station are
                    disconnected, after the charging session is authorized to stop.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT EVConnectedPostSession then execute Reusable State
                            EVConnectedPostSession

Main

1. The Test System notifies the CSMS about the status change of the connector.
   Message: StatusNotificationRequest
   - connectorStatus is Available
   Message: NotifyEventRequest
   - trigger is Delta
   - actualValue is Available
   - component.name is Connector
   - variable.name is AvailabilityState
2. The CSMS responds accordingly.
3. The Test System sends a TransactionEventRequest With triggerReason is EVCommunicationLost
   transactionInfo.chargingState is Idle
   transactionInfo.stoppedReason is EVDisconnected
   eventType is Ended
4. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVDisconnected
"""
