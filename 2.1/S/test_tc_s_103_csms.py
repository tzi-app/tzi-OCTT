"""
Test case name      Battery Swap - Remote Start - enough batteries available
Test case Id        TC_S_103_CSMS
Use case Id(s)      S02, S03, S04
Requirement(s)      N/a
System under test   CSMS

Description         CSMS is able to support battery swapping.

Purpose             To verify whether the CSMS is able successful support battery swapping.

Prerequisite(s)     Charging Station supports battery swapping.
                    There are enough batteries available for swapping.

Configuration State BatterySwapCtrlr.Idtoken is <not set>

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Let CSMS trigger a request for swapping batteries

1. The CSMS sends a RequestBatterySwapRequest
2. The Test System responds with a RequestBatterySwapResponse with
    - status Accepted

Note: Set of two (virtual) batteries are inserted at this point in scenario.

3. The Test System notifies the CSMS about the status change of the slot.
4. The CSMS responds accordingly.
5. The Test System sends a TransactionEventRequest with
    - eventType Started
    - triggerReason CablePluggedIn
    - idToken.idToken ""
    - idToken.type NoAuthorization
    - evse <Configured evseId>
    - evse.connectorId 1
    - transactionInfo.transactionId 111-222-333-444-3
    - transactionInfo.chargingState EVConnected
6. The CSMS responds with a TransactionEventResponse
7. The Test System notifies the CSMS about the status change of the slot.
8. The CSMS responds accordingly.
9. The Test System sends a TransactionEventRequest with
    - eventType Started
    - triggerReason CablePluggedIn
    - idToken.idToken ""
    - idToken.type NoAuthorization
    - evse <Configured evseId2>
    - evse.connectorId 1
    - transactionInfo.transactionId 111-222-333-444-4
    - transactionInfo.chargingState EVConnected
10. The CSMS responds with a TransactionEventResponse
11. The Test System sends a BatterySwapRequest with
    - eventType BatteryIn
    - requestId <requestId>
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - batteryData[0].evseId <Configured evseId>_
    - batteryData[0].serialNumber 1234
    - batteryData[0].soC 23
    - batteryData[0].soH 85
    - batteryData[1].evseId <Configured evseId2>_
    - batteryData[1].serialNumber 5678
    - batteryData[1].soC 45
    - batteryData[1].soH 87
12. The CSMS responds with a BatterySwapResponse

Note: Set of two batteries are extracted at this point in scenario.

13. The Charging Station sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason EnergyLimitReached
    - idToken.idToken ""
    - idToken.type NoAuthorization
    - transactionInfo.transactionId 111-222-333-444-1
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
14. The Test System responds with a TransactionEventResponse
15. The Test System notifies the CSMS about the status change of the slot.
16. The CSMS responds accordingly.
17. The Charging Station sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason EnergyLimitReached
    - idToken.idToken ""
    - idToken.type NoAuthorization
    - transactionInfo.transactionId 111-222-333-444-2
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
18. The Test System responds with a TransactionEventResponse
19. The Test System notifies the CSMS about the status change of the slot.
20. The CSMS responds accordingly.
21. The Test System sends a BatterySwapRequest with
    - eventType BatteryOut
    - requestId <requestId>
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - batteryData[0].evseId <Configured evseId3>_
    - batteryData[0].serialNumber 4321
    - batteryData[0].soC 80
    - batteryData[0].soH 95
    - batteryData[1].evseId <Configured evseId4>_
    - batteryData[1].serialNumber 8765
    - batteryData[1].soC 85
    - batteryData[1].soH 78
22. The CSMS responds with a BatterySwapResponse

Note: Steps 13 and 14 are repeated for each battery taken out

Tool validations
* Step 1:
    Message: RequestBatterySwapResponse
    - requestId must be <not omitted>
    - idToken.idToken must be <Configured valid_idtoken_idtoken>
* Step 6:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
* Step 10:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
* Step 12:
    Message: BatterySwapResponse
* Step 14:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
* Step 18:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
* Step 22:
    Message: BatterySwapResponse

Post scenario validations:
    N/a

Remarks
Transcriber's notes on the printed layout (not text from the PDF): In the scenario table, steps 13 and 17
("The Charging Station sends a TransactionEventRequest") are printed in the Charging Station column and steps
14 and 18 ("The Test System responds with a TransactionEventResponse") are printed in the CSMS column. The
Requirement(s) cell is printed empty. The Step 1 tool validation names the message RequestBatterySwapResponse,
although step 1 is the CSMS sending a RequestBatterySwapRequest. All of this is transcribed as printed.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.22. Page 1365 - 1367 - (2026-02) - TC_S_103_CSMS - Test case updated
        | Test case name | Battery Swap - Remote Start - enough batteries available |
        | Test case Id | TC_S_103_CSMS |
        | Prerequisite(s) | Charging Station supports battery swapping. / There are enough batteries available
          for swapping. / BatterySwapCtrlr.Idtoken is <not set> |

        | Before (Preparations) |
        | Configuration State: / [removed: BatterySwapCtrlr.Idtoken is <not set>] / N/a |
        | Memory State: / N/a |
        | Reusable State(s): / N/a |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Manual Action: Let CSMS trigger a request for swapping batteries | |
        | 2. The Test System responds with a RequestBatterySwapResponse with / status Accepted | 1. The CSMS
          sends a RequestBatterySwapRequest |
        | Note: Set of two (virtual) batteries are inserted at this point in scenario. | |
        | 3. The Test System notifies the CSMS about the status change of the slot. / connectorStatus Occupied
          | 4. The CSMS responds accordingly. |
        | 5. The Test System sends a TransactionEventRequest with / eventType Started / triggerReason
          CablePluggedIn / idToken.idToken "" / idToken.type NoAuthorization / evse [removed: <Configured
          evseId>] <i> / evse.connectorId 1 / transactionInfo.transactionId [removed: 111-222-333-444-3]
          <transactionId> / transactionInfo.chargingState EVConnected | 6. The CSMS responds with a
          TransactionEventResponse |
        | [removed: 7. The Test System notifies the CSMS about the status change of the slot.] | [removed: 8.
          The CSMS responds accordingly.] |
        | [removed: 9. The Test System sends a TransactionEventRequest with] / [removed: eventType Started] /
          [removed: triggerReason CablePluggedIn] / [removed: idToken.idToken ""] / [removed: idToken.type
          NoAuthorization] / [removed: evse <Configured evseId2>] / [removed: evse.connectorId 1] / [removed:
          transactionInfo.transactionId 111-222-333-444-4] / [removed: transactionInfo.chargingState
          EVConnected] | [removed: 10. The CSMS responds with a TransactionEventResponse] |
        | Note : Steps 3 through 6 are repeated for each battery inserted | |
        | [removed: 11.] 7. The Test System sends a BatterySwapRequest with / eventType BatteryIn / requestId
          <requestId> / idToken.idToken <Configured valid_idtoken_idtoken> / batteryData[0].evseId [removed:
          <Configured evseId>] 1 / batteryData[0].serialNumber 1234 / batteryData[0].soC 23 /
          batteryData[0].soH 85 / batteryData[1].evseId [removed: <Configured evseId2>] 2 /
          batteryData[1].serialNumber 5678 / batteryData[1].soC 45 / batteryData[1].soH 87 | [removed: 12.] 8.
          The CSMS responds with a BatterySwapResponse |
        | Note: Set of two batteries are extracted at this point in scenario. | |

        | Main (Test scenario) | |
        | [removed: 13. The Charging Station sends a TransactionEventRequest with] / [removed: eventType
          Ended] / [removed: triggerReason EnergyLimitReached] / [removed: idToken.idToken ""] / [removed:
          idToken.type NoAuthorization] / [removed: transactionInfo.transactionId 111-222-333-444-1] /
          [removed: transactionInfo.chargingState Idle] / [removed: transactionInfo.stoppedReason
          EVDisconnected] | [removed: 14. The Test System responds with a TransactionEventResponse] |
        | [removed: 15.] 9. The Test System notifies the CSMS about the status change of the slot. /
          connectorStatus Available | [removed: 16.] 10. The CSMS responds accordingly. |
        | [removed: 17.] 11. The Charging Station sends a TransactionEventRequest with / eventType Ended /
          triggerReason [removed: EnergyLimitReached] EVCommunicationLost / idToken.idToken "" / idToken.type
          NoAuthorization / transactionInfo.transactionId [removed: 111-222-333-444-2] <transactionId> /
          transactionInfo.chargingState Idle / transactionInfo.stoppedReason EVDisconnected | [removed: 18.]
          12. The Test System responds with a TransactionEventResponse |
        | [removed: 19. The Test System notifies the CSMS about the status change of the slot.] | [removed:
          20. The CSMS responds accordingly.] |
        | Note : Steps 9 through 12 are repeated for each battery taken out | |
        | [removed: 21.] 13. The Test System sends a BatterySwapRequest with / eventType BatteryOut /
          requestId <requestId> / idToken.idToken <Configured valid_idtoken_idtoken> / batteryData[0].evseId
          [removed: <Configured evseId3>] 3 / batteryData[0].serialNumber 4321 / batteryData[0].soC 80 /
          batteryData[0].soH 95 / batteryData[1].evseId [removed: <Configured evseId4>] 4 /
          batteryData[1].serialNumber 8765 / batteryData[1].soC 85 / batteryData[1].soH 78 | [removed: 22.]
          14. The CSMS responds with a BatterySwapResponse |
        | Note: [removed: Steps 13 and 14 are repeated for each battery taken out] | |

        | Tool validations |
        | * Step 1: / Message: [removed: RequestBatterySwapResponse] RequestBatterySwapRequest / - requestId
          must be <not omitted> / - idToken.idToken must be <Configured valid_idtoken_idtoken> / * Step 6: /
          Message: TransactionEventResponse / - idTokenInfo.status must be Accepted / [removed: * Step 10:] /
          [removed: Message: TransactionEventResponse] / [removed: - idTokenInfo.status must be Accepted] /
          [removed: * Step 12:] / [removed: Message: BatterySwapResponse] / * [removed: Step 14:] Step 12: /
          Message: TransactionEventResponse / - idTokenInfo.status must be Accepted / [removed: * Step 18:] /
          [removed: Message: TransactionEventResponse] / [removed: - idTokenInfo.status must be Accepted] /
          [removed: * Step 22:] / [removed: Message: BatterySwapResponse] |
"""
