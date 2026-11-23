"""
Test case name      Set Charging Profile - Resuming transaction after interruption - TxResumptionTimeout not
                    expired - TxAllowEnergyTransferResumption is true
Test case Id        TC_E_117_CSMS
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

Configuration State SmartChargingCtrlr.ChargingProfilePersistence is <absent>

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

The Test System disconnects the connection.
The Test System waits the <Configured transaction duration>
The Test System restores the connection.

3. The Test System sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The Test System notifies the CSMS about the current state of all connectors.
    Message: NotifyEventRequest
    - eventData[0].trigger Delta
    - eventData[0].component.name "Connector"
    - eventData[0].variable.name "AvailabilityState"
    Configured EVSE.Connector:
    - eventData[0].actualValue "Occupied"
    Other connectors:
    - eventData[0].actualValue "Available"
6. The CSMS responds accordingly.
7 The Test System sends a SecurityEventNotificationRequest
    - type must be StartupOfTheDevice OR ResetOrReboot
8 The CSMS responds with a SecurityEventNotificationResponse
9 The Test System sends a NotifyEventRequest
    - eventData.trigger = Delta
    - eventData.transactionId = <transactionId from this transaction>
    - eventData.eventNotificationType = HardWiredNotification
    - eventData.severity = 3
    - eventData.actualValue = true
    - eventData.component.name = ElectricalFeed
    - eventData.variable.name = Problem
10 The CSMS responds with a NotifyEventResponse
11 The Test System sends a NotifyEventRequest
    Same content as step 9, but with actualValue = false:
    - eventData.actualValue = false
12 The CSMS responds with a NotifyEventResponse
13. The Test System sends a TransactionEventRequest
    - eventType Updated
    - triggerReason TxResumed
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.chargingState Charging
14. The CSMS responds with a TransactionEventResponse
15. The CSMS sends a SetChargingProfileRequest
16. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose must be TxProfile
* Step 4:
    Message: BootNotificationResponse
    - status must be Accepted
* Step 15:
    Message: SetChargingProfileRequest must contain an identical chargingProfile as in Step 1 or identical as
             of time of Step 15.

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.4. Page 1100/1101 - (2026-02) - TC_E_117_CSMS - Updated prerequisites and SetChargingProfileRequest
        tool validations
        The configuration SmartChargingCtrlr.ChargingProfilePersistence is <absent> was moved to Prerequisites
        and SetChargingProfileRequest tool validations were updated.

        | Test case name | Set Charging Profile - Resuming transaction after interruption -
          TxResumptionTimeout not expired - TxAllowEnergyTransferResumption is true |
        | Test case Id | TC_E_117_CSMS |
        | … | |
        | Prerequisite(s) | SmartChargingCtrlr.ChargingProfilePersistence is <absent> /
          TxCtrlr.TxResumptionTimeout is 999 / TxCtrlr.TxAllowEnergyTransferResumption is true |

        | Before (Preparations) |
        | Configuration State: / [removed: SmartChargingCtrlr.ChargingProfilePersistence is <absent>] / N/a |
        | … |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 7. The Test System sends a SecurityEventNotificationRequest / - type must be [removed:
          StartupOfTheDevice OR] ResetOrReboot | 8. The CSMS responds with a SecurityEventNotificationResponse
          |
        | … | |

        | Tool validations |
        | … / * Step 15: / [removed: Message: SetChargingProfileRequest must contain an identical
          chargingProfile as in Step 1 or identical as of time of Step 15.] / Message:
          SetChargingProfileRequest / - chargingProfile.chargingProfilePurpose must be TxProfile |
"""
