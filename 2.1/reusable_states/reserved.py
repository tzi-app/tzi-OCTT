"""
State               Reserved
System under test   CSMS
Description         This state will simulate a reservation for a specified evse.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Trigger the CSMS to send a ReserveNowRequest for specific EVSE.

1. The CSMS sends a ReserveNowRequest
2. The Test System responds with a ReserveNowResponse With status Accepted
3. The Test System notifies the CSMS about the current state of the connector(s) of the Specified EVSE
   Message: StatusNotificationRequest
   with connectorStatus Reserved
   Message: NotifyEventRequest
   with trigger Delta
   actualValue "Reserved"
   component.name "Connector"
   variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1: Message: ReserveNowRequest
  - evseId must be <Specified evseId>
  - connectorType must be omitted
  - idToken.idToken <Configured valid_idtoken_idtoken>
  - idToken.type <Configured valid_idtoken_type>
Post condition      State is Reserved
"""

import os

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from trigger import send_call

VALID_ID_TOKEN = os.environ['VALID_ID_TOKEN']
VALID_ID_TOKEN_TYPE = os.environ['VALID_ID_TOKEN_TYPE']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])
CONFIGURED_CONNECTOR_ID = int(os.environ['CONFIGURED_CONNECTOR_ID'])

# How long the reservations of the test cases are valid, in seconds
RESERVATION_DURATION = 300


def reserve_now_payload(reservation_id=1, evse_id=None, connector_type=None, group_id_token=None,
                        expires_in=RESERVATION_DURATION):
    """The ReserveNowRequest that the Manual Action "Trigger the CSMS to send a
    ReserveNowRequest" asks the CSMS for: a reservation for the configured valid idToken."""
    payload = {
        'id': reservation_id,
        'expiryDateTime': utc_now_iso(expires_in),
        'idToken': {'idToken': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    }
    if evse_id is not None:
        payload['evseId'] = evse_id
    if connector_type is not None:
        payload['connectorType'] = connector_type
    if group_id_token is not None:
        payload['groupIdToken'] = group_id_token
    return payload


def validate_reserve_now_request(request, evse_id=None, connector_type=None):
    """The tool validations of a ReserveNowRequest: evseId and connectorType as given (None:
    must be omitted), and the configured valid idToken."""
    if evse_id is None:
        assert request.evse_id is None, f"ReserveNowRequest.evseId must be omitted, got {request.evse_id}"
    else:
        assert request.evse_id == evse_id, f"Expected ReserveNowRequest.evseId {evse_id}, got {request.evse_id}"
    if connector_type is None:
        assert request.connector_type is None, \
            f"ReserveNowRequest.connectorType must be omitted, got {request.connector_type}"
    else:
        assert request.connector_type == connector_type, \
            f"Expected ReserveNowRequest.connectorType {connector_type}, got {request.connector_type}"
    assert request.id_token.id_token == VALID_ID_TOKEN, \
        f"Expected ReserveNowRequest.idToken.idToken {VALID_ID_TOKEN}, got {request.id_token.id_token}"
    assert request.id_token.type == VALID_ID_TOKEN_TYPE, \
        f"Expected ReserveNowRequest.idToken.type {VALID_ID_TOKEN_TYPE}, got {request.id_token.type}"


async def reserved(cp: TziChargePoint21, evse_id: int = CONFIGURED_EVSE_ID,
                   connector_id: int = CONFIGURED_CONNECTOR_ID, reservation_id: int = 1):
    """Returns the ReserveNowRequest of the CSMS."""
    # Manual Action: Trigger the CSMS to send a ReserveNowRequest for specific EVSE.
    # 1. The CSMS sends a ReserveNowRequest
    # 2. The Test System responds with a ReserveNowResponse With status Accepted
    cp.set_response('ReserveNow', status='Accepted')
    request = await cp.wait_for_request(
        'ReserveNow',
        manual_action=send_call(cp.id, 'ReserveNow',
                                reserve_now_payload(reservation_id, evse_id=evse_id)))
    validate_reserve_now_request(request, evse_id=evse_id)

    # 3. The Test System notifies the CSMS about the current state of the connector(s) of the
    #    Specified EVSE
    #    Message: StatusNotificationRequest with connectorStatus Reserved
    #    Message: NotifyEventRequest with trigger Delta, actualValue "Reserved",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_connector_status('Reserved', evse_id=evse_id, connector_id=connector_id)
    return request
