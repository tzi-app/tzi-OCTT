"""
State               Unavailable
System under test   CSMS
Description         This state will simulate that Charging Station / EVSEs / connectors are set to
                    AvailabilityState Unavailable.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Request the CSMS to change the availability of the specified components to Inoperative.

1. The CSMS sends a ChangeAvailabilityRequest
2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
3. The Test System notifies the CSMS about the current state of all connectors belonging to the specified EVSE
   (and optionally also from the EVSE itself).
   Message: StatusNotificationRequest
   - connectorStatus Unavailable
   Message: NotifyEventRequest
   - trigger Delta
   - actualValue "Unavailable"
   - component.name "ChargingStation" / EVSE / Connector
   - variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 1: Message ChangeAvailabilityRequest
  - operationalStatus Inoperative
  - evse <Specified evseId>
  - connectorId omitted
Post condition      State is Unavailable
"""

from charge_point import CONFIGURED_CONNECTOR_ID, CONFIGURED_NUMBER_OF_EVSES, TziChargePoint21
from trigger import send_call


async def unavailable(cp: TziChargePoint21, evse_id: int = None, connector_id: int = None):
    """Set the specified components to Unavailable: the Charging Station (no evse_id), an EVSE
    (evse_id) or a connector (evse_id and connector_id)."""
    payload = {'operationalStatus': 'Inoperative'}
    if evse_id is not None:
        payload['evse'] = {'id': evse_id}
        if connector_id is not None:
            payload['evse']['connectorId'] = connector_id

    # Manual Action: Request the CSMS to change the availability of the specified components
    #                to Inoperative.
    # 1. The CSMS sends a ChangeAvailabilityRequest
    # 2. The Test System responds with a ChangeAvailabilityResponse with status Accepted
    cp.set_response('ChangeAvailability', status='Accepted')
    request = await cp.wait_for_request(
        'ChangeAvailability', manual_action=send_call(cp.id, 'ChangeAvailability', payload))
    assert request.operational_status == 'Inoperative', \
        f"Expected ChangeAvailabilityRequest.operationalStatus Inoperative, got {request.operational_status}"
    if evse_id is None:
        assert request.evse is None, \
            f"ChangeAvailabilityRequest.evse must be omitted for the Charging Station, got {request.evse}"
    else:
        assert request.evse is not None and request.evse.id == evse_id, \
            f"Expected ChangeAvailabilityRequest.evse.id {evse_id}, got {request.evse}"
        assert request.evse.connector_id == connector_id, \
            f"Expected ChangeAvailabilityRequest.evse.connectorId " \
            f"{'omitted' if connector_id is None else connector_id}, got {request.evse.connector_id}"

    # 3. The Test System notifies the CSMS about the current state of all connectors belonging
    #    to the specified EVSE (and optionally also from the EVSE itself).
    #    Message: StatusNotificationRequest - connectorStatus Unavailable
    #    Message: NotifyEventRequest - trigger Delta, actualValue "Unavailable", component.name
    #             "ChargingStation" / EVSE / Connector, variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    evse_ids = range(1, CONFIGURED_NUMBER_OF_EVSES + 1) if evse_id is None else [evse_id]
    for id_of_evse in evse_ids:
        await cp.send_connector_status(
            'Unavailable', evse_id=id_of_evse,
            connector_id=CONFIGURED_CONNECTOR_ID if connector_id is None else connector_id)
