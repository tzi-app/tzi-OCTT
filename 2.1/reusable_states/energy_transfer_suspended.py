"""
State               EnergyTransferSuspended
System under test   CSMS
Description         This state will simulate that the Charging Station is in a state where the energy transfer
                    is suspended by the EV.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      If State is NOT EnergyTransferStarted then execute Reusable State
                            EnergyTransferStarted

Main

Notes(s): The tool will wait for <Configured Transaction Duration> seconds

1. The Test System sends a TransactionEventRequest With triggerReason is ChargingStateChanged
   transactionInfo.chargingState is SuspendedEV
2. The CSMS responds with a TransactionEventResponse

Tool validations
N/a
Post condition      State is EnergyTransferSuspended
"""
