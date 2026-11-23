"""
Test case name      Resuming transaction after interruption - TxResumptionTimeout not expired -
                    TxAllowEnergyTransferResumption is true
Test case Id        TC_E_113_CSMS
Use case Id(s)      E17
Requirement(s)      E17.FR.15

Requirement Details:
    E17.FR.15: CSMS SHALL send the SetChargingProfileRequest for chargingProfilePurpose = TxProfile for these
               transactions again.
        Precondition: E17.FR.14 AND CSMS has a charging profile of chargingProfilePurpose = TxProfile for
                      transactions reported with triggerReason = TxResumed AND
                      SmartChargingCtrlr.ChargingProfilePersistence for instance = "TxProfile" = false or
                      absent
        Note: The charging profiles are identical to those sent at start of transaction, since start time of
              the resumed transaction has not changed.
System under test   CSMS

Description         CSMS restores TxProfile after Charging Station resumes transactions which had a Charging
                    profile with purpose TxProfile configured.

Purpose             To verify the CSMS restores the charging profile for a transaction after resuming
                    transactions by the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
The Test System disconnects the connection.
The Test System waits the <Configured transaction duration>
The Test System restores the connection.

1. The Test System sends a BootNotificationRequest
2. The CSMS responds with a BootNotificationResponse
3. The Test System notifies the CSMS about the current state of all connectors.
    Message: NotifyEventRequest
    - eventData[0].trigger Delta
    - eventData[0].component.name "Connector"
    - eventData[0].variable.name "AvailabilityState"
    Configured EVSE.Connector:
    - eventData[0].actualValue "Occupied"
    Other connectors:
    - eventData[0].actualValue "Available"
4. The CSMS responds accordingly.
5 The Test System sends a SecurityEventNotificationRequest
    - type must be StartupOfTheDevice OR ResetOrReboot
6 The CSMS responds with a SecurityEventNotificationResponse
7 The Test System sends a NotifyEventRequest
    - eventData.trigger = Delta
    - eventData.transactionId = <transactionId from this transaction>
    - eventData.eventNotificationType = HardWiredNotification
    - eventData.severity = 3
    - eventData.actualValue = true
    - eventData.component.name = ElectricalFeed
    - eventData.variable.name = Problem
8 The CSMS responds with a NotifyEventResponse
9 The Test System sends a NotifyEventRequest
    Same content as step 7, but with actualValue = false:
    - eventData.actualValue = false
10 The CSMS responds with a NotifyEventResponse
11. The Test System sends a TransactionEventRequest
    - eventType Updated
    - triggerReason TxResumed
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.chargingState Charging
12. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a
"""
