"""Helpers for the authorization checks in the OCPP 2.1 tests."""

import os
from datetime import datetime, timezone

from device_model import find_variable
from trigger import set_variables

# How far a "current date/time" of the CSMS may be from the clock of the Test System, in seconds
CURRENT_TIME_TOLERANCE = 60


def is_current_date_time(value):
    """Whether an OCPP dateTime is the current date/time, within CURRENT_TIME_TOLERANCE."""
    moment = datetime.fromisoformat(value.upper().replace('Z', '+00:00'))
    return abs((moment - datetime.now(timezone.utc)).total_seconds()) <= CURRENT_TIME_TOLERANCE


async def set_master_pass_group_id(cp):
    """The first two steps of the Master Pass test cases (TC_C_47, TC_C_48, TC_C_49) since
    errata 2026-09 (6.3.1). The Test System no longer has a configured masterPassGroupId: the
    CSMS provides it.

    Manual action: trigger CSMS to set the masterPassGroupId
    1. The CSMS sends a SetVariablesRequest with
       - variable.name = "MasterPassGroupId"
       - component.name = "AuthCtrlr"
       - attributeValue = <Specified masterPassGroupId>
    2. The Charging Station responds with SetVariablesResponse with attributeStatus = Accepted

    Returns the masterPassGroupId of step 1, for the tool validations of the later steps.
    """
    cp.set_variable_status = 'Accepted'
    request = await cp.wait_for_request(
        'SetVariables',
        manual_action=set_variables(cp.id, [{
            'component': {'name': 'AuthCtrlr'},
            'variable': {'name': 'MasterPassGroupId'},
            'attributeValue': os.environ['MASTERPASS_GROUP_ID'],
        }]))
    set_variable = find_variable(request.set_variable_data, 'AuthCtrlr', 'MasterPassGroupId')
    assert set_variable is not None, \
        f"Expected AuthCtrlr.MasterPassGroupId in setVariableData, got: {request.set_variable_data}"
    assert set_variable.attribute_value, "The masterPassGroupId must not be empty"
    return set_variable.attribute_value


def validate_id_token_info(message, id_token_info, status='Accepted', group_id=None):
    """Check the idTokenInfo of a response.

    message:  the name of the response, for the failure text
    status:   the expected idTokenInfo.status, or a tuple of allowed statuses
    group_id: the expected idTokenInfo.groupIdToken.idToken, when the step validates it
    """
    assert id_token_info is not None, f"{message} has no idTokenInfo"
    allowed = (status,) if isinstance(status, str) else tuple(status)
    assert id_token_info.status in allowed, \
        f"Expected {message}.idTokenInfo.status {' or '.join(allowed)}, got {id_token_info.status}"
    if group_id is not None:
        assert id_token_info.group_id_token is not None, \
            f"{message}.idTokenInfo has no groupIdToken; expected {group_id}"
        assert id_token_info.group_id_token.id_token == group_id, \
            f"Expected {message}.idTokenInfo.groupIdToken.idToken {group_id}, " \
            f"got {id_token_info.group_id_token.id_token}"
