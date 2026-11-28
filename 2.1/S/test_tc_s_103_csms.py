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

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import ChargingSession, TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']

# The slots (EVSEs) of the battery swap station: the batteries that the EV Driver brings go
# into slots 1 and 2, the charged batteries come out of slots 3 and 4.
BATTERIES_IN = [
    {'evse_id': 1, 'serial_number': '1234', 'soc': 23, 'soh': 85},
    {'evse_id': 2, 'serial_number': '5678', 'soc': 45, 'soh': 87},
]
BATTERIES_OUT = [
    {'evse_id': 3, 'serial_number': '4321', 'soc': 80, 'soh': 95},
    {'evse_id': 4, 'serial_number': '8765', 'soc': 85, 'soh': 78},
]
# The idToken of the transaction of a battery in a slot
NO_AUTHORIZATION = {'id_token': '', 'type': 'NoAuthorization'}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_s_103(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Prerequisites (errata 2026-09, 6.3.22): Charging Station supports battery swapping. There
    # are enough batteries available for swapping. BatterySwapCtrlr.Idtoken is <not set>
    cp.variables = {'BatterySwapCtrlr.Available': 'true', 'BatterySwapCtrlr.Enabled': 'true'}
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The scenario is the one of errata 2026-09 (6.3.22).
    valid_id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # Manual Action: Let CSMS trigger a request for swapping batteries
    # 1. The CSMS sends a RequestBatterySwapRequest
    # 2. The Test System responds with a RequestBatterySwapResponse with
    #    - status Accepted
    cp.set_response('RequestBatterySwap', status='Accepted')
    request = await cp.wait_for_request(
        'RequestBatterySwap',
        manual_action=send_call(BASIC_AUTH_CP, 'RequestBatterySwap', {
            'idToken': {'idToken': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
            'requestId': 1,
        }))
    assert request.request_id is not None, "RequestBatterySwapRequest.requestId must not be omitted"
    assert request.id_token.id_token == VALID_ID_TOKEN, \
        f"Expected RequestBatterySwapRequest.idToken.idToken {VALID_ID_TOKEN}, " \
        f"got {request.id_token.id_token}"

    # Note: Set of two (virtual) batteries are inserted at this point in scenario.
    # Note: Steps 3 through 6 are repeated for each battery inserted
    for battery in BATTERIES_IN:
        # 3. The Test System notifies the CSMS about the status change of the slot.
        #    - connectorStatus Occupied
        # 4. The CSMS responds accordingly.
        await cp.send_connector_status('Occupied', evse_id=battery['evse_id'], connector_id=1)

        # 5. The Test System sends a TransactionEventRequest with
        #    - eventType Started
        #    - triggerReason CablePluggedIn
        #    - idToken.idToken ""
        #    - idToken.type NoAuthorization
        #    - evse <i>
        #    - evse.connectorId 1
        #    - transactionInfo.transactionId <transactionId>
        #    - transactionInfo.chargingState EVConnected
        # 6. The CSMS responds with a TransactionEventResponse
        slot = ChargingSession()
        transaction_id = slot.start_transaction()
        response = await cp.call(call.TransactionEvent(
            event_type='Started',
            timestamp=utc_now_iso(),
            trigger_reason='CablePluggedIn',
            seq_no=slot.next_seq_no(),
            transaction_info={'transaction_id': transaction_id, 'charging_state': 'EVConnected'},
            id_token=NO_AUTHORIZATION,
            evse={'id': battery['evse_id'], 'connector_id': 1},
        ))
        validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')

    # 7. The Test System sends a BatterySwapRequest with
    #    - eventType BatteryIn
    #    - requestId <requestId>
    #    - idToken.idToken <Configured valid_idtoken_idtoken>
    #    - batteryData[0]: evseId 1, serialNumber 1234, soC 23, soH 85
    #    - batteryData[1]: evseId 2, serialNumber 5678, soC 45, soH 87
    # 8. The CSMS responds with a BatterySwapResponse
    await cp.call(call.BatterySwap(
        event_type='BatteryIn', request_id=request.request_id, id_token=valid_id_token,
        battery_data=BATTERIES_IN))

    # Note: Set of two batteries are extracted at this point in scenario.
    # Note: Steps 9 through 12 are repeated for each battery taken out
    for battery in BATTERIES_OUT:
        # 9.  The Test System notifies the CSMS about the status change of the slot.
        #     - connectorStatus Available
        # 10. The CSMS responds accordingly.
        await cp.send_connector_status('Available', evse_id=battery['evse_id'], connector_id=1)

        # 11. The Charging Station sends a TransactionEventRequest with
        #     - eventType Ended
        #     - triggerReason EVCommunicationLost
        #     - idToken.idToken ""
        #     - idToken.type NoAuthorization
        #     - transactionInfo.transactionId <transactionId>
        #     - transactionInfo.chargingState Idle
        #     - transactionInfo.stoppedReason EVDisconnected
        #     It is the transaction in which this battery was charged, which started before this
        #     scenario: the event is not the first one of its transaction.
        # 12. The CSMS responds with a TransactionEventResponse
        slot = ChargingSession()
        transaction_id = slot.start_transaction()
        for _ in range(3):
            slot.next_seq_no()
        response = await cp.call(call.TransactionEvent(
            event_type='Ended',
            timestamp=utc_now_iso(),
            trigger_reason='EVCommunicationLost',
            seq_no=slot.next_seq_no(),
            transaction_info={
                'transaction_id': transaction_id,
                'charging_state': 'Idle',
                'stopped_reason': 'EVDisconnected',
            },
            id_token=NO_AUTHORIZATION,
        ))
        validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')

    # 13. The Test System sends a BatterySwapRequest with
    #     - eventType BatteryOut
    #     - requestId <requestId>
    #     - idToken.idToken <Configured valid_idtoken_idtoken>
    #     - batteryData[0]: evseId 3, serialNumber 4321, soC 80, soH 95
    #     - batteryData[1]: evseId 4, serialNumber 8765, soC 85, soH 78
    # 14. The CSMS responds with a BatterySwapResponse
    await cp.call(call.BatterySwap(
        event_type='BatteryOut', request_id=request.request_id, id_token=valid_id_token,
        battery_data=BATTERIES_OUT))

    start_task.cancel()
