"""
State               EVConnectedPostSession
System under test   CSMS
Description         This state will simulate that the Charging Station is in a state where the energy transfer
                    has been stopped and the transaction is NOT authorized to resume energy transfer without
                    re-authorization.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT StopAuthorized then execute Reusable State StopAuthorized

Main

1. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is EVConnected
   eventType is Updated
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EVConnectedPostSession
"""
