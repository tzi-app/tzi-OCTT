"""
Reusable states for OCPP 1.6 tests.
Each function brings the charge point into a known state and returns
the relevant data for subsequent test steps.
"""

from ocpp.v16.enums import (
    AuthorizationStatus,
    ChargePointStatus,
    RegistrationStatus,
)


async def booted(cp):
    """Reusable State: Booted (Table 199).
    Sends BootNotification + StatusNotification(Available) for connector 0 and 1.
    Returns the boot_response.
    """
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    for connector_id in (0, 1):
        await cp.send_status_notification(connector_id, status=ChargePointStatus.available)

    return boot_response


async def authorized(cp, id_tag):
    """Reusable State: Authorized (Table 200).
    Sends Authorize.req with the given idTag.
    Returns the authorize_response.
    """
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted
    return auth_response


async def charging(cp, id_tag, connector_id=1):
    """Reusable State: Charging (Table 201).
    Prerequisite: authorized() must have been called first.
    Sends StatusNotification(Preparing) → StartTransaction → StatusNotification(Charging).
    Returns (start_response, transaction_id).
    """
    await cp.send_status_notification(connector_id, status=ChargePointStatus.preparing)

    start_response = await cp.send_start_transaction(connector_id, id_tag)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    transaction_id = start_response.transaction_id

    await cp.send_status_notification(connector_id, status=ChargePointStatus.charging)

    return start_response, transaction_id
