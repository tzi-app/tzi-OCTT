"""
Test case name      Reset ImmediateAndResume - With Ongoing Transaction - Resuming Energy Transfer
Test case Id        TC_B_103_CSMS
Use case Id(s)      B13
Requirement(s)      B13.FR.31

Requirement Details:
    B13.FR.31: CSMS SHALL send the SetChargingProfileRequest for chargingProfilePurpose = TxProfile for these
               transactions again.
        Precondition: B13.FR.30 AND CSMS has a charging profile of chargingProfilePurpose = TxProfile for
                      transactions reported with triggerReason = TxResumed AND
                      SmartChargingCtrlr.ChargingProfilePersistence for instance = "TxProfile" = false or
                      absent
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset
                    itself by sending a ResetRequest during a transaction. When ResetRequest "Immediate" is
                    send the charging stations will try to stop all transactions before rebooting.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the Charging Station with status ImmediateAndResume

1. The CSMS sends a ResetRequest
    with status ImmediateAndResume
2. The Test System responds with a ResetResponse
    with status Accepted
3. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason ResetCommand
    - idToken is omitted
4. The CSMS responds with a TransactionEventResponse.
5. The Test System sends a BootNotificationRequest
    with reason RemoteReset
6. The CSMS responds with a BootNotificationResponse
7. The Test System notifies the CSMS about the current state of all connectors.
    For <Configured connectorId>:
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    For <Other connector(s)>:
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
8. The CSMS responds accordingly.
9 The Test System sends a SecurityEventNotificationRequest
    with
    - type ResetOrReboot
10 The CSMS responds with a SecurityEventNotificationResponse
11. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason TxResumed
    - transactionInfo.chargingState Charging
    - idToken is omitted
12. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 1:
    Message ResetRequest
    - type ImmediateAndResume
* Step 6:
    Message BootNotificationResponse
    - status Accepted

Post scenario validations:
    - N/a
"""
