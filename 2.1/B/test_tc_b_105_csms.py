"""
Test case name      Set new NetworkConnectionProfile - Add new NetworkConfiguration using SetVariables
Test case Id        TC_B_105_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.29. B09.FR.30

Requirement Details:
    B09.FR.29 (2.1): CSMS SHALL set variable ApnEnabled resp. VpnEnabled of NetworkConfiguration to True.
        Precondition: When CSMS configures variables for an APN or VPN connection
    B09.FR.30 (2.1): CSMS SHALL set variable ApnEnabled resp. VpnEnabled of NetworkConfiguration to False.
        Precondition: When CSMS does not configure variables for an APN or VPN connection
System under test   Charging Station

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify that CSMS can set NetworkConfiguration and correctly sets the value of
                    Apn/VpnEnabled.

Prerequisite(s)     CSMS is able to set the NetworkConfiguration component
                    Test System reports NetworkConfiguration variables as ReadWrite.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: In the following steps <configurationSlot> equals <Configured non-active configurationSlot>
Note: Request CSMS to set a network configuration that includes APN connection details, but no VPN details.

1. CSMS sends a SetVariablesRequest on component NetworkConfiguration[<Configured non-active
   configurationSlot>]
2. The Charging Station responds with SetVariablesResponse(s) with
    - setVariableResult.attributeStatus = Accepted for each variable

Tool validations
* Step 2: (The following can be sent in one or multiple messages.)
    Message SetVariablesRequest for
    component NetworkConfiguration[<Configured non-active configurationSlot>] with:
    - OcppCsmsUrl = <Configured ocppCsmsUrl>
    - OcppInterface = Any
    - OcppTransport = JSON
    - OcppVersion = OCPP21
    - MessageTimeout = <Configured messageTimeout>
    - SecurityProfile = 2
    - Identity = <Configured charging station identity>
    - BasicAuthPassword = PasswordOfSufficientLength
    - VpnEnabled = false
    - ApnEnabled = true
    - Apn = <Configured APN URL>
    - ApnUserName = <Configured APN username>
    - ApnPassword = <Configured APN password>
    - ApnAuthentication one of PAP, CHAP, NONE, AUTO

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.5. Page 1006 - (2026-02) - TC_B_105_CSMS - Manual action added
        The note before step 1. has been changed to indicate a manual action is required.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | [removed: Note: Request CSMS to set a network configuration that includes APN connection details,
          but no VPN details.] | |
        | Manual action : Request CSMS to set a network configuration that includes APN connection details,
          but no VPN details. | |
        | 2. The [removed: Charging Station] Test system responds with / SetVariablesResponse(s) with / -
          setVariableResult.attributeStatus = Accepted for each variable | 1. CSMS sends a SetVariablesRequest
          on component / NetworkConfiguration[<Configured non-active configurationSlot>] |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from trigger import set_network_configuration
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_NON_ACTIVE_CONFIGURATION_SLOT = int(os.environ['CONFIGURED_NON_ACTIVE_CONFIGURATION_SLOT'])
CONFIGURED_MESSAGE_TIMEOUT = int(os.environ['CONFIGURED_MESSAGE_TIMEOUT'])
CONFIGURED_OCPP_CSMS_URL = os.environ['CSMS_ADDRESS']
CONFIGURED_APN = os.environ['CONFIGURED_APN']
CONFIGURED_APN_USERNAME = os.environ['CONFIGURED_APN_USERNAME']
CONFIGURED_APN_PASSWORD = os.environ['CONFIGURED_APN_PASSWORD']

BASIC_AUTH_PASSWORD = 'PasswordOfSufficientLength'
APN_AUTHENTICATIONS = ('PAP', 'CHAP', 'NONE', 'AUTO')

# The network configuration the CSMS is requested to set: APN connection details, and no VPN
# details.
NETWORK_CONFIGURATION = {
    'ocppCsmsUrl': CONFIGURED_OCPP_CSMS_URL,
    'ocppInterface': 'Any',
    'ocppTransport': 'JSON',
    'ocppVersion': 'OCPP21',
    'messageTimeout': CONFIGURED_MESSAGE_TIMEOUT,
    'securityProfile': 2,
    'identity': BASIC_AUTH_CP,
    'basicAuthPassword': BASIC_AUTH_PASSWORD,
    'apn': {
        'apn': CONFIGURED_APN,
        'apnUserName': CONFIGURED_APN_USERNAME,
        'apnPassword': CONFIGURED_APN_PASSWORD,
        'apnAuthentication': 'AUTO',
    },
}

# The variables of the component NetworkConfiguration the CSMS has to set, with their values.
# VpnEnabled and ApnEnabled are not in the requested configuration: the CSMS sets them
# because it configures an APN connection and no VPN connection (B09.FR.29, B09.FR.30).
EXPECTED_VARIABLES = {
    'OcppCsmsUrl': CONFIGURED_OCPP_CSMS_URL,
    'OcppInterface': 'Any',
    'OcppTransport': 'JSON',
    'OcppVersion': 'OCPP21',
    'MessageTimeout': str(CONFIGURED_MESSAGE_TIMEOUT),
    'SecurityProfile': '2',
    'Identity': BASIC_AUTH_CP,
    'BasicAuthPassword': BASIC_AUTH_PASSWORD,
    'VpnEnabled': 'false',
    'ApnEnabled': 'true',
    'Apn': CONFIGURED_APN,
    'ApnUserName': CONFIGURED_APN_USERNAME,
    'ApnPassword': CONFIGURED_APN_PASSWORD,
}


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_b_105(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual action: Request CSMS to set a network configuration that includes APN connection
    #                details, but no VPN details.
    # 1. CSMS sends a SetVariablesRequest on component NetworkConfiguration[<Configured
    #    non-active configurationSlot>]
    # 2. The Test System responds with SetVariablesResponse(s) with
    #    setVariableResult.attributeStatus = Accepted for each variable
    cp.set_variable_status = 'Accepted'
    requests_before = len(cp.requests_of('SetVariables'))
    await cp.wait_for_request(
        'SetVariables',
        manual_action=set_network_configuration(
            BASIC_AUTH_CP, CONFIGURED_NON_ACTIVE_CONFIGURATION_SLOT, NETWORK_CONFIGURATION))
    # The variables can be sent in one or multiple messages. The Manual Action is done, so
    # the CSMS has sent them all.
    requests = cp.requests_of('SetVariables')[requests_before:]

    slot = str(CONFIGURED_NON_ACTIVE_CONFIGURATION_SLOT)
    values = {}
    for request in requests:
        for item in request.set_variable_data:
            if item.component.name == 'NetworkConfiguration' and item.component.instance == slot:
                values[item.variable.name] = item.attribute_value

    for variable, expected in EXPECTED_VARIABLES.items():
        assert variable in values, \
            f"The CSMS did not set NetworkConfiguration[{slot}].{variable}; it set: {sorted(values)}"
        actual = values[variable]
        if expected in ('true', 'false'):
            actual = actual.lower()
        assert actual == expected, \
            f"Expected NetworkConfiguration[{slot}].{variable} = {expected}, got: {values[variable]}"
    assert values.get('ApnAuthentication') in APN_AUTHENTICATIONS, \
        f"Expected ApnAuthentication one of {APN_AUTHENTICATIONS}, got: {values.get('ApnAuthentication')}"

    start_task.cancel()
