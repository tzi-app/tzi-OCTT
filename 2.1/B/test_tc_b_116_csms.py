"""
Test case name      Reset ImmediateAndResume - With Ongoing Transaction and SmartCharging - resuming
                    energytransfer
Test case Id        TC_B_116_CSMS
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
                    sent the charging stations will try to stop all transactions before rebooting.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual action: trigger CSMS to set a Charging Profile of type TxProfile on <transactionId>

1. The CSMS sends a SetChargingProfileRequest
2. The Test System responds with a SetChargingProfileResponse with status Accepted

Manual Action: Request the CSMS to reboot the Charging Station with status ImmediateAndResume

3. The CSMS sends a ResetRequest
4. The Test System responds with a ResetResponse with status Accepted
5. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason ResetCommand
6. The CSMS responds with a TransactionEventResponse.
7. The Test System sends a BootNotificationRequest with reason RemoteReset
8. The CSMS responds with a BootNotificationResponse
9. The Test System notifies the CSMS about the current state of all connectors.
    For <Configured connectorId>:
    Message: StatusNotificationRequest
    - connectorStatus Occupied
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Occupied"
    - component.name "Connector"
    - variable.name "AvailabilityState"
    For <Other connector(s)>:
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
10. The CSMS responds accordingly.
11. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason TxResumed
    - idToken is omitted
12. The CSMS responds with a TransactionEventResponse.
13. The CSMS sends a SetChargingProfileRequest
14. The Test System responds with a SetChargingProfileResponse with status Accepted

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - chargingProfile.chargingProfilePurpose TxProfile
* Step 3:
    Message ResetRequest
    - type ImmediateAndResume
* Step 8:
    Message BootNotificationResponse
    - status Accepted
* Step 13:
    Message: SetChargingProfileRequest must either contain an identical chargingProfile as in Step 1 or
             identical from the time of step 11 onwards.

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.7. Page 1007/1008 - (2026-02) - TC_B_116_CSMS -
        Added SecurityEventNotificationRequest steps and updated tool validations.

        | Test case name | Reset ImmediateAndResume - With Ongoing Transaction and SmartCharging - resuming
          energytransfer |
        | Test case Id | TC_B_116_CSMS |
        | … | |
        | Description | This test case covers how the CSMS can remotely request the Charging Station to reset
          itself by sending a ResetRequest during a transaction. When ResetRequest [removed: "Immediate"]
          "ImmediateAndResume" is sent the charging stations will try to stop all transactions before
          rebooting. |

        | Main / (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | 9. The Test System notifies the CSMS about the current state of all connectors. / For <Configured
          connectorId>: / [removed: Message: StatusNotificationRequest] / [removed: - connectorStatus
          Occupied] / Message: NotifyEventRequest / - trigger Delta / - actualValue "Occupied" / -
          component.name "Connector" / - variable.name "AvailabilityState" /  / For <Other connector(s)>: /
          [removed: Message: StatusNotificationRequest] / [removed: - connectorStatus Available] / Message:
          NotifyEventRequest / - trigger Delta / - actualValue "Available" / - component.name "Connector" / -
          variable.name "AvailabilityState" | 10. The CSMS responds accordingly. |

        | Main / (Test scenario) | |
        | 11. The Test System sends a SecurityEventNotificationRequest with / - type ResetOrReboot | 12. The
          CSMS responds with a SecurityEventNotificationResponse |
        | [removed: 11.] 13. The Test System sends a TransactionEventRequest. / - eventType Updated / -
          triggerReason TxResumed / - idToken is omitted | [removed: 12.] 14. The CSMS responds with a
          TransactionEventResponse. |
        | [removed: 14.] 16. The Test System responds with a SetChargingProfileResponse / with status Accepted
          | [removed: 13.] 15. The CSMS sends a SetChargingProfileRequest |

        | Tool validations |
        | * Step 1: / … * Step [removed: 13] 15: / [removed: Message: SetChargingProfileRequest must either
          contain an identical chargingProfile as in Step 1 or identical from the time of step 11 onwards.] /
          Message: SetChargingProfileRequest / - chargingProfile.chargingProfilePurpose TxProfile |
"""
