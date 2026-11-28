"""
Test case name      Start transaction options - DataSigned
Test case Id        TC_E_11_CSMS
Use case Id(s)      E01(S4)
Requirement(s)      E01.FR.04

Requirement Details:
    E01.FR.04: The Charging Station SHALL start a transaction and send a TransactionEventRequest (eventType =
               Started) to the CSMS.
        Precondition: TxStartPoint contains: DataSigned AND The Charging Station has a meter that can sign
                      measured values AND Configuration Variable: SampledDataSignReadings set to true. AND The
                      Charging Station has retrieved a signed meter value AND No transaction has started yet
System under test   CSMS

Description         OCPP 2.x.x has a flexible transaction mechanism that allows the transaction start and stop
                    points to be configured differently. This test covers one of the start options.

Purpose             To verify if the CSMS is able to handle a Charging Station that starts a transaction when
                    the signed meter values are received.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends an AuthorizeRequest
    With idToken.idToken <Configured valid_idtoken_idtoken>
    idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System notifies the CSMS about the status change of the connector.
    Message: StatusNotificationRequest
    - connectorStatus is Occupied
    Message: NotifyEventRequest
    - trigger is Delta
    - actualValue is Occupied
    - component.name is Connector
    - variable.name is AvailabilityState
4. The CSMS responds accordingly.
5. The Test System sends a TransactionEventRequest
    With eventType is Started
    triggerReason is SignedDataReceived
    idToken.idToken <Configured valid_idtoken_idtoken>
    idToken.type <Configured valid_idtoken_type>
    evse.id is <Configured evseId>
    evse.connectorId is <Configured connectorId>
    meterValue is provided with the following values:
    sampledValue.value is 0.0
    sampledValue.context is Transaction.Begin
    sampledValue.signedMeterValue is <Generated SignedMeterValueType>
6. The CSMS responds with a TransactionEventResponse
7. The Test System sends a TransactionEventRequest
    With eventType is Updated
    triggerReason is ChargingStateChanged
    transactionInfo.chargingState is Charging
8. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 6:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted

Post scenario validations:
    N/a
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import TziChargePoint21
from metering import signed_meter_value
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_e_11(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    id_token = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}

    # 1. The Test System sends an AuthorizeRequest
    #    With idToken.idToken <Configured valid_idtoken_idtoken>
    #    idToken.type <Configured valid_idtoken_type>
    # 2. The CSMS responds with an AuthorizeResponse
    response = await cp.call(call.Authorize(id_token=id_token))
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')

    # 3. The Test System notifies the CSMS about the status change of the connector.
    #    Message: StatusNotificationRequest - connectorStatus is Occupied
    #    Message: NotifyEventRequest - trigger is Delta, actualValue is Occupied,
    #             component.name is Connector, variable.name is AvailabilityState
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Occupied', evse_id=CONFIGURED_EVSE_ID,
                                   connector_id=CONFIGURED_CONNECTOR_ID)

    # 5. The Test System sends a TransactionEventRequest
    #    With eventType is Started
    #    triggerReason is SignedDataReceived
    #    idToken.idToken <Configured valid_idtoken_idtoken>
    #    idToken.type <Configured valid_idtoken_type>
    #    evse.id is <Configured evseId>
    #    evse.connectorId is <Configured connectorId>
    #    meterValue is provided with the following values:
    #    sampledValue.value is 0.0
    #    sampledValue.context is Transaction.Begin
    #    sampledValue.signedMeterValue is <Generated SignedMeterValueType>
    # 6. The CSMS responds with a TransactionEventResponse
    transaction_id = cp.session.start_transaction()
    meter_timestamp = utc_now_iso()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='SignedDataReceived',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=id_token,
        evse={'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID},
        meter_value=[{
            'timestamp': meter_timestamp,
            'sampled_value': [{
                'value': 0.0,
                'context': 'Transaction.Begin',
                'signed_meter_value': signed_meter_value(0.0, meter_timestamp,
                                                         context='Transaction.Begin'),
            }],
        }],
    ))
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')

    # 7. The Test System sends a TransactionEventRequest
    #    With eventType is Updated
    #    triggerReason is ChargingStateChanged
    #    transactionInfo.chargingState is Charging
    # 8. The CSMS responds with a TransactionEventResponse
    await cp.call(call.TransactionEvent(
        event_type='Updated',
        timestamp=utc_now_iso(),
        trigger_reason='ChargingStateChanged',
        seq_no=cp.next_seq_no(),
        transaction_info={'transaction_id': transaction_id, 'charging_state': 'Charging'},
    ))

    start_task.cancel()
