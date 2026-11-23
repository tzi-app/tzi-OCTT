"""
State               EnergyTransferStarted
System under test   CSMS
Description         This state will simulate that there is transferring energy between the EV and EVSE of the
                    simulated Charging Station.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT Authorized then execute Reusable State Authorized
                            If EVConnected is true, then proceed to part 2
                            Else proceed to part 1.

Main

Main (Part 1)

1. The Test System notifies the CSMS about the status change of the connector.
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
   eventType is Updated
4. The CSMS responds with a TransactionEventResponse

Main (Part 2)

5. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is Charging
   eventType is Updated
6. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EnergyTransferStarted
                    EVConnected is true
"""
