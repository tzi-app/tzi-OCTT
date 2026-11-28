"""
Test case name      Upgrade Charging Station Security Profile - Accepted
Test case Id        TC_A_19_CSMS
Use case Id(s)      A05
Requirement(s)      A05.FR.04, A05.FR.07

Requirement Details:
    A05.FR.04: The Charging Station SHALL respond with SetVariablesResponse(Accepted)
        Precondition: The Charging Station receives SetVariablesRequest for NetworkConfigurationPriority
                      containing profile slots for NetworkConnectionProfiles with a 'securityProfile' value
                      equal to or higher than the current value AND all prerequisites are met
    A05.FR.07: The CSMS SHALL NOT allow the Charging Station to connect with a lower security profile anymore.
        Precondition: A05.FR.06
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station, to increase the security
                    profile level.

Purpose             To verify if the CSMS is able to set a new network connection profile at one of the by the
                    Charging Station defined configuration slots with a higher security profile than currently
                    configured.

Prerequisite(s)     - Security profile must be set to 1 or 2.
                    - If Security profile is set to 1, then a trusted certificate must be installed.

Configuration State N/a

Memory State        If configured <Security profile> is 2, then RenewChargingStationCertificate
                    The Test System uses this certificate during the TLS handshake when connecting with
                    security profile 3.

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to set a new NetworkConnectionProfile with a security profile level one higher
               than currently configured

1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse With status Accepted

Manual Action: Request the CSMS to change the NetworkConfigurationPriority to one that contains the
               configurationSlot of the new NetworkConnectionProfile from step 1

3. The CSMS sends a SetVariablesRequest
4. The Test System responds with a SetVariablesResponse with status Accepted

Manual Action: Request the CSMS to reboot the Charging Station

5. The CSMS sends a ResetRequest
6. The Test System responds with a ResetResponse with status Accepted
7. The Test System reconnects to the CSMS using the new NetworkProfile, containing the upgraded security
   profile <Configured securityProfile + 1>.
8. The CSMS accepts the connection attempt.
9. Execute Reusable State Booted
10. The Test System reconnects to the CSMS using the original NetworkProfile, containing the lower security
    profile.
    Note(s):
    - This is done to ensure that the CSMS does not accept a connection using the lower security profile
      anymore.
11. The CSMS shall not accept the connection attempt.
12. The Test System reconnects to the CSMS using the new NetworkProfile, containing the upgraded security
    profile <Configured securityProfile + 1>.
    Note(s):
    - This is done to restore the connection before ending the testcase.
13. The CSMS accepts the connection attempt.

Tool validations
* Step 1:
    Message SetNetworkProfileRequest
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile + 1>
* Step 3:
    Message SetVariablesRequest
    setVariableData:
    - variable.name = "NetworkConfigurationPriority"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = <contains configurationSlot provided at step 1>
* Step 11:
    When upgrading a Charging Station to a higher security profile, a CSMS has several options regarding which
    endpoint to use. This affects the way the CSMS is able to detect it needs to reject the incoming
    connection attempt.

    In case of having upgraded from security profile 2 to 3, but there is an incoming connection attempt using
    security profile 2:
    When the same endpoint is used, then it depends on the CSMS endpoint configuration.
    - When the CSMS does a full switch and only allows TLS handshakes when a client certificate is provided,
      then the TLS handshake is rejected.
    - When the CSMS only requires this Charging Station to use a client certificate, then it accepts the TLS
      handshake (because it will be unable to detect which Charging Station is connecting) and it rejects the
      HTTP request to establish the WebSocket connection.

    When a different port or a whole different endpoint is used for the upgrade, then on the original endpoint
    the CSMS accepts the TLS handshake and it rejects the HTTP request to establish the WebSocket connection
    (because this Charging Station is not allowed to connect with security profile 2 anymore).

    In case of security profile 1, the case is always the same. The CSMS shall always reject the HTTP request
    to establish the WebSocket connection, because TLS is required for this Charging Station.

Post scenario validations:
    The Test System and the CSMS are connected.
"""

import asyncio
import logging
import os
import ssl

import pytest
from websockets import InvalidStatusCode
from websockets.exceptions import InvalidMessage

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.renew_charging_station_certificate import renew_charging_station_certificate
from security import client_certificate_files, connect_with_profile
from trigger import send_call, set_security_profile

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
SECURITY_PROFILE_2_CP = os.environ['CP21_SP2']
CONFIGURED_CONFIGURATION_SLOT = int(os.environ['CONFIGURED_CONFIGURATION_SLOT'])
CONFIGURED_MESSAGE_TIMEOUT = int(os.environ['CONFIGURED_MESSAGE_TIMEOUT'])
CONFIGURED_OCPP_INTERFACE = os.environ['CONFIGURED_OCPP_INTERFACE']


@pytest.mark.asyncio
async def test_tc_a_19():
    # The upgrade from security profile 2 to 3. The upgrade from 1 to 2 cannot be told apart
    # here, because this suite runs security profile 1 over TLS as well.
    cp_id = SECURITY_PROFILE_2_CP
    security_profile = 2
    new_security_profile = security_profile + 1

    # Prerequisite: the security profile is 2. An earlier run may have left the station at 3.
    await set_security_profile(cp_id, security_profile)

    try:
        ws = await connect_with_profile(cp_id, security_profile)
        try:
            cp = TziChargePoint21(cp_id, ws)
            start_task = asyncio.create_task(cp.start())

            # Memory State: the configured security profile is 2, so
            # RenewChargingStationCertificate. The Test System uses this certificate during
            # the TLS handshake when connecting with security profile 3.
            certificate_chain, private_key = await renew_charging_station_certificate(cp)

            # Manual Action: Request the CSMS to set a new NetworkConnectionProfile with a
            #                security profile level one higher than currently configured
            # 1. The CSMS sends a SetNetworkProfileRequest
            # 2. The Test System responds with a SetNetworkProfileResponse With status Accepted
            set_network_profile = await cp.wait_for_request(
                'SetNetworkProfile',
                manual_action=send_call(cp_id, 'SetNetworkProfile', {
                    'configurationSlot': CONFIGURED_CONFIGURATION_SLOT,
                    'connectionData': {
                        'messageTimeout': CONFIGURED_MESSAGE_TIMEOUT,
                        'ocppCsmsUrl': CSMS_ADDRESS,
                        'ocppInterface': CONFIGURED_OCPP_INTERFACE,
                        'ocppTransport': 'JSON',
                        'ocppVersion': 'OCPP20',
                        'securityProfile': new_security_profile,
                    },
                }))
            configuration_slot = set_network_profile.configuration_slot
            connection_data = set_network_profile.connection_data
            assert connection_data.message_timeout == CONFIGURED_MESSAGE_TIMEOUT, \
                f"Expected messageTimeout {CONFIGURED_MESSAGE_TIMEOUT}, got: {connection_data.message_timeout}"
            assert connection_data.ocpp_interface == CONFIGURED_OCPP_INTERFACE, \
                f"Expected ocppInterface {CONFIGURED_OCPP_INTERFACE}, got: {connection_data.ocpp_interface}"
            assert connection_data.ocpp_transport == 'JSON', \
                f"Expected ocppTransport JSON, got: {connection_data.ocpp_transport}"
            assert connection_data.ocpp_version == 'OCPP20', \
                f"Expected ocppVersion OCPP20, got: {connection_data.ocpp_version}"
            assert connection_data.security_profile == new_security_profile, \
                f"Expected securityProfile {new_security_profile}, got: {connection_data.security_profile}"

            # Manual Action: Request the CSMS to change the NetworkConfigurationPriority to
            #                one that contains the configurationSlot of the new
            #                NetworkConnectionProfile from step 1
            # 3. The CSMS sends a SetVariablesRequest
            # 4. The Test System responds with a SetVariablesResponse with status Accepted
            set_variables = await cp.wait_for_request(
                'SetVariables',
                manual_action=send_call(cp_id, 'SetVariables', {
                    'setVariableData': [{
                        'attributeValue': str(configuration_slot),
                        'component': {'name': 'OCPPCommCtrlr'},
                        'variable': {'name': 'NetworkConfigurationPriority'},
                    }],
                }))
            set_variable = set_variables.set_variable_data[0]
            assert set_variable.variable.name == 'NetworkConfigurationPriority', \
                f"Expected variable.name NetworkConfigurationPriority, got: {set_variable.variable.name}"
            assert set_variable.component.name == 'OCPPCommCtrlr', \
                f"Expected component.name OCPPCommCtrlr, got: {set_variable.component.name}"
            assert str(configuration_slot) in set_variable.attribute_value.split(','), \
                f"Expected attributeValue to contain configurationSlot {configuration_slot}, " \
                f"got: {set_variable.attribute_value}"

            # Manual Action: Request the CSMS to reboot the Charging Station
            # 5. The CSMS sends a ResetRequest
            # 6. The Test System responds with a ResetResponse with status Accepted
            await cp.wait_for_request(
                'Reset', manual_action=send_call(cp_id, 'Reset', {'type': 'OnIdle'}))

            start_task.cancel()
        finally:
            await ws.close()

        # The station now uses the upgraded security profile.
        await set_security_profile(cp_id, new_security_profile)

        with client_certificate_files(certificate_chain, private_key) as (new_cert, new_key):
            # 7. The Test System reconnects to the CSMS using the new NetworkProfile,
            #    containing the upgraded security profile <Configured securityProfile + 1>.
            # 8. The CSMS accepts the connection attempt.
            ws = await connect_with_profile(
                cp_id, new_security_profile, client_cert=new_cert, client_key=new_key)
            try:
                assert ws.open, "The CSMS must accept the connection with the upgraded security profile"
                cp = TziChargePoint21(cp_id, ws)
                start_task = asyncio.create_task(cp.start())

                # 9. Execute Reusable State Booted
                await booted(cp)

                start_task.cancel()
            finally:
                await ws.close()

            # 10. The Test System reconnects to the CSMS using the original NetworkProfile,
            #     containing the lower security profile.
            # 11. The CSMS shall not accept the connection attempt. Having upgraded from
            #     security profile 2 to 3, the CSMS either rejects the TLS handshake (it only
            #     allows TLS handshakes with a client certificate), or it accepts the TLS
            #     handshake and rejects the HTTP request to establish the WebSocket
            #     connection.
            with pytest.raises((InvalidStatusCode, ssl.SSLError, ConnectionError, InvalidMessage)) as rejected:
                ws_old = await connect_with_profile(cp_id, security_profile)
                await ws_old.close()
            logging.info(f"CSMS rejected the connection with security profile {security_profile}: "
                         f"{rejected.value!r}")

            # 12. The Test System reconnects to the CSMS using the new NetworkProfile,
            #     containing the upgraded security profile <Configured securityProfile + 1>.
            # 13. The CSMS accepts the connection attempt.
            ws = await connect_with_profile(
                cp_id, new_security_profile, client_cert=new_cert, client_key=new_key)
            try:
                # Post scenario validation: the Test System and the CSMS are connected.
                assert ws.open, "The CSMS must accept the connection with the upgraded security profile"
            finally:
                await ws.close()
    finally:
        # Restore the configured security profile, so that other tests are not affected
        await set_security_profile(cp_id, security_profile)
