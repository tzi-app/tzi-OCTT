"""
Test case name      Upgrade Charging Station Security Profile - Accepted
Test case Id        TC_A_19_CSMS
Use case Id(s)      A05
Requirement(s)      A05.FR.04, A05.FR.07

Requirement Details:
    A05.FR.04: The Charging Station receives SetVariablesRequest for NetworkConfigurationPriority containing profile slots for NetworkConnectionProfiles with a 'securityProfile' value equal to or higher than the current value AND all prerequisites are met The Charging Station SHALL respond with SetVariablesResponse(Accepted)
        Precondition: The Charging Station receives SetVariablesRequest for NetworkConfigurationPriority containing profile slots for NetworkConnectionProfiles with a 'securityProfile' value equal to or higher than the current value AND all prerequisites are met
    A05.FR.07: The Charging Station SHALL send a SecurityEventNotification to the CSMS to notify of certificate installation.
        Precondition: A05.FR.06
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station, to increase the security
                    profile level.

Purpose             To verify if the CSMS is able to set a new network connection profile at one of the by the
                    Charging Station defined configuration slots with a higher security profile than currently
                    configured.

Prerequisite(s)     - Security profile must be set to 1 or 2.
                    - If Security profile is set to 1, then a trusted certificate must be installed.

Memory State        If configured <Security profile> is 2, then RenewChargingStationCertificate

Test Scenario
Manual Action: Request the CSMS to set a new NetworkConnectionProfile with a security profile level
one higher than currently configured

1. The CSMS sends a SetNetworkProfileRequest with:
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppCsmsUrl <Configured ocppCsmsUrl>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile + 1>
2. The OCTT responds with a SetNetworkProfileResponse with status Accepted

Manual Action: Request the CSMS to change the NetworkConfigurationPriority to one that contains
the configurationSlot of the new NetworkConnectionProfile from step 1

3. The CSMS sends a SetVariablesRequest with:
    setVariableData:
    - variable.name = "NetworkConfigurationPriority"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = <contains configurationSlot provided at step 1>
4. The OCTT responds with a SetVariablesResponse with status Accepted

Manual Action: Request the CSMS to reboot the Charging Station

5. The CSMS sends a ResetRequest
6. The OCTT responds with a ResetResponse with status Accepted
7. The OCTT reconnects to the CSMS with security profile is <Configured securityProfile + 1>
8. The CSMS accepts the connection attempt.
9. Execute Reusable State Booted
10. The OCTT reconnects to the CSMS with security profile is <Configured securityProfile>
11. The CSMS shall not accept the connection attempt.
12. The OCTT reconnects to the CSMS with security profile is <Configured securityProfile + 1>
13. The CSMS accepts the connection attempt.

Tool validations
* Step 1:
    Message SetNetworkProfileRequest
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppCsmsUrl <Configured ocppCsmsUrl>
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

Post scenario validations:
    The OCTT and the CSMS are connected.
"""

import asyncio
import os
import ssl
import time
import logging

import pytest
import websockets
from websockets import InvalidStatusCode

from ocpp.v201.enums import (
    RegistrationStatusEnumType, ConnectorStatusEnumType,
    SetVariableStatusEnumType, ResetStatusEnumType,
    SetNetworkProfileStatusEnumType,
    GenericStatusEnumType, CertificateSignedStatusEnumType,
    CertificateSigningUseEnumType,
)

from tzi_charge_point import TziChargePoint
from trigger import trigger_v201, send_call, set_security_profile
from utils import (
    get_basic_auth_headers, create_ssl_context,
    generate_csr, save_private_key_to_temp, save_cert_chain_to_temp,
)

logging.basicConfig(level=logging.INFO)

CSMS_ADDRESS = os.environ['CSMS_ADDRESS']
BASIC_AUTH_CP = os.environ['CP201_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
TLS_CA_CERT = os.environ['TLS_CA_CERT']
TLS_CLIENT_CERT = os.environ['TLS_CLIENT_CERT']
TLS_CLIENT_KEY = os.environ['TLS_CLIENT_KEY']
SECURITY_PROFILE_2_CP = os.environ['CP201_SP2']
SECURITY_PROFILE_3_CP = os.environ['CP201_SP3']
CSMS_ACTION_TIMEOUT = int(os.environ['CSMS_ACTION_TIMEOUT'])


async def connect_with_profile(cp_id, security_profile, client_cert=None, client_key=None):
    """Connect to CSMS using the specified security profile."""
    if security_profile == 1:
        # SP1: Basic Auth over WSS (TLS server cert only, no client cert)
        uri = f'{CSMS_ADDRESS}/{cp_id}'
        ssl_ctx = create_ssl_context(ca_cert=TLS_CA_CERT)
        headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
        return await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )
    elif security_profile == 2:
        # SP2: Basic Auth over WSS (TLS)
        uri = f'{CSMS_ADDRESS}/{cp_id}'
        ssl_ctx = create_ssl_context(ca_cert=TLS_CA_CERT)
        headers = get_basic_auth_headers(cp_id, BASIC_AUTH_CP_PASSWORD)
        return await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            extra_headers=headers,
            ssl=ssl_ctx,
        )
    elif security_profile == 3:
        # SP3: Client Cert over WSS (mTLS, no basic auth)
        uri = f'{CSMS_ADDRESS}/{cp_id}'
        ssl_ctx = create_ssl_context(
            ca_cert=TLS_CA_CERT,
            client_cert=client_cert or TLS_CLIENT_CERT,
            client_key=client_key or TLS_CLIENT_KEY,
        )
        return await websockets.connect(
            uri=uri,
            subprotocols=['ocpp2.0.1'],
            ssl=ssl_ctx,
        )
    else:
        raise ValueError(f"Unsupported security profile: {security_profile}")


async def renew_charging_station_certificate(cp_id, ws, timeout):
    """Execute Reusable State RenewChargingStationCertificate.
    Returns (new_cert_path, new_key_path) for the renewed certificate.
    """
    cp = TziChargePoint(cp_id, ws)
    cp._certificate_signed_response_status = CertificateSignedStatusEnumType.accepted
    start_task = asyncio.create_task(cp.start())

    # Trigger CSMS to send TriggerMessageRequest(SignChargingStationCertificate)
    asyncio.create_task(trigger_v201(cp_id, 'trigger-message', {
        'requestedMessage': 'SignChargingStationCertificate',
    }))

    await asyncio.wait_for(
        cp._received_trigger_message.wait(),
        timeout=timeout,
    )
    assert cp._trigger_message_data == 'SignChargingStationCertificate', \
        f"Expected SignChargingStationCertificate, got: {cp._trigger_message_data}"

    # Generate a real CSR
    csr_pem, private_key = generate_csr(cp_id)

    sign_response = await cp.send_sign_certificate_request(
        csr=csr_pem,
        certificate_type=CertificateSigningUseEnumType.charging_station_certificate,
    )
    assert sign_response.status == GenericStatusEnumType.accepted, \
        f"Expected SignCertificateResponse Accepted, got: {sign_response.status}"

    # Wait for CertificateSignedRequest
    await asyncio.wait_for(
        cp._received_certificate_signed.wait(),
        timeout=timeout,
    )
    assert cp._certificate_signed_data is not None
    assert cp._certificate_signed_data['certificate_chain'], \
        "CertificateSignedRequest must contain a certificate chain"

    new_cert_path = save_cert_chain_to_temp(cp._certificate_signed_data['certificate_chain'])
    new_key_path = save_private_key_to_temp(private_key)

    logging.info(f"Certificate renewal complete (chain length="
                 f"{len(cp._certificate_signed_data['certificate_chain'])})")

    start_task.cancel()
    return new_cert_path, new_key_path


@pytest.mark.asyncio
@pytest.mark.parametrize("initial_security_profile", [2])
async def test_tc_a_19(initial_security_profile):
    new_security_profile = initial_security_profile + 1
    new_client_cert = None
    new_client_key = None

    if initial_security_profile == 1:
        cp_id = BASIC_AUTH_CP
    else:
        cp_id = SECURITY_PROFILE_2_CP

    # Ensure the station starts at the expected security profile (self-healing from dirty state)
    await set_security_profile(cp_id, initial_security_profile)

    # Memory State: If configured security profile is 2, execute RenewChargingStationCertificate.
    # The resulting certificate is used during TLS handshake when connecting with security profile 3.
    if initial_security_profile == 2:
        ws_renew = await connect_with_profile(cp_id, initial_security_profile)
        time.sleep(0.5)
        new_client_cert, new_client_key = await renew_charging_station_certificate(
            cp_id, ws_renew, CSMS_ACTION_TIMEOUT,
        )
        await ws_renew.close()
        logging.info("Memory State: RenewChargingStationCertificate completed")

    try:
        # Connect with current security profile
        ws = await connect_with_profile(cp_id, initial_security_profile)
        time.sleep(0.5)

        cp = TziChargePoint(cp_id, ws)
        cp._set_network_profile_response_status = SetNetworkProfileStatusEnumType.accepted
        cp._set_variables_response_status = SetVariableStatusEnumType.accepted
        cp._reset_response_status = ResetStatusEnumType.accepted
        start_task = asyncio.create_task(cp.start())

        # Steps 1-2: Trigger CSMS to send SetNetworkProfileRequest
        asyncio.create_task(send_call(cp_id, 'SetNetworkProfile', {
            'configurationSlot': 1,
            'connectionData': {
                'messageTimeout': 30,
                'ocppCsmsUrl': CSMS_ADDRESS,
                'ocppInterface': 'Wired0',
                'ocppTransport': 'JSON',
                'ocppVersion': 'OCPP20',
                'securityProfile': new_security_profile,
            },
        }))

        await asyncio.wait_for(
            cp._received_set_network_profile.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        assert cp._set_network_profile_data is not None
        conn_data = cp._set_network_profile_data['connection_data']
        configuration_slot = cp._set_network_profile_data['configuration_slot']

        # Validate SetNetworkProfileRequest content
        security_profile_value = conn_data.get('security_profile',
                                               conn_data.get('securityProfile'))
        assert security_profile_value == new_security_profile, \
            f"Expected securityProfile {new_security_profile}, got: {security_profile_value}"

        transport_value = conn_data.get('ocpp_transport', conn_data.get('ocppTransport'))
        assert transport_value == 'JSON', \
            f"Expected ocppTransport JSON, got: {transport_value}"

        version_value = conn_data.get('ocpp_version', conn_data.get('ocppVersion'))
        assert version_value == 'OCPP20', \
            f"Expected ocppVersion OCPP20, got: {version_value}"

        # Validate messageTimeout is present
        message_timeout = conn_data.get('message_timeout', conn_data.get('messageTimeout'))
        assert message_timeout is not None, \
            "SetNetworkProfileRequest must contain connectionData.messageTimeout"

        # Validate ocppInterface is present
        ocpp_interface = conn_data.get('ocpp_interface', conn_data.get('ocppInterface'))
        assert ocpp_interface is not None, \
            "SetNetworkProfileRequest must contain connectionData.ocppInterface"

        logging.info(f"Received SetNetworkProfileRequest: slot={configuration_slot}, "
                     f"securityProfile={new_security_profile}, "
                     f"messageTimeout={message_timeout}, ocppInterface={ocpp_interface}")

        # Steps 3-4: Trigger CSMS to send SetVariablesRequest (NetworkConfigurationPriority)
        cp._received_set_variables.clear()
        asyncio.create_task(send_call(cp_id, 'SetVariables', {
            'setVariableData': [{
                'attributeValue': str(configuration_slot),
                'component': {'name': 'OCPPCommCtrlr'},
                'variable': {'name': 'NetworkConfigurationPriority'},
            }],
        }))

        await asyncio.wait_for(
            cp._received_set_variables.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        assert cp._set_variables_data is not None
        set_var = cp._set_variables_data[0]
        assert set_var.get('variable', {}).get('name') == 'NetworkConfigurationPriority', \
            f"Expected NetworkConfigurationPriority variable, got: {set_var}"
        assert set_var.get('component', {}).get('name') == 'OCPPCommCtrlr', \
            f"Expected OCPPCommCtrlr component, got: {set_var}"

        attr_value = set_var.get('attribute_value', set_var.get('attributeValue', ''))
        assert str(configuration_slot) in str(attr_value), \
            f"Expected attributeValue to contain configurationSlot {configuration_slot}, got: {attr_value}"

        logging.info(f"Received SetVariablesRequest: NetworkConfigurationPriority = {attr_value}")

        # Steps 5-6: Trigger CSMS to send ResetRequest
        asyncio.create_task(send_call(cp_id, 'Reset', {
            'type': 'Immediate',
        }))

        await asyncio.wait_for(
            cp._received_reset.wait(),
            timeout=CSMS_ACTION_TIMEOUT,
        )

        logging.info(f"Received ResetRequest: {cp._reset_data}")

        # Close current connection (simulating reboot)
        start_task.cancel()
        await ws.close()

        # Persist the new security profile in the CSMS DB (simulates operator completing upgrade)
        await set_security_profile(cp_id, new_security_profile)

        # Steps 7-8: Reconnect with NEW security profile - CSMS should accept
        ws = await connect_with_profile(
            cp_id, new_security_profile,
            client_cert=new_client_cert, client_key=new_client_key,
        )
        time.sleep(0.5)
        assert ws.open, "CSMS should accept connection with new security profile"

        # Step 9: Execute Reusable State Booted
        cp = TziChargePoint(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # SP3 requires serialNumber matching certificate CN (B01.FR.12)
        if new_security_profile == 3:
            boot_response = await cp.send_boot_notification_with_serial(cp_id)
        else:
            boot_response = await cp.send_boot_notification()
        assert boot_response.status == RegistrationStatusEnumType.accepted

        await cp.send_status_notification(1, ConnectorStatusEnumType.available)
        await cp.send_notify_event([{
            'event_id': 1,
            'timestamp': '2024-01-01T00:00:00Z',
            'trigger': 'Delta',
            'actual_value': 'Available',
            'event_notification_type': 'HardWiredNotification',
            'component': {'name': 'Connector'},
            'variable': {'name': 'AvailabilityState'},
        }])

        start_task.cancel()
        await ws.close()

        # Steps 10-11: Reconnect with OLD security profile - CSMS should REJECT
        try:
            ws_old = await connect_with_profile(cp_id, initial_security_profile)
            time.sleep(0.5)
            if ws_old.open:
                await ws_old.close()
                pytest.fail(
                    f"CSMS should NOT accept connection with old security profile "
                    f"{initial_security_profile}"
                )
        except (InvalidStatusCode, ssl.SSLError, ConnectionRefusedError,
                ConnectionResetError, OSError) as e:
            logging.info(
                f"CSMS correctly rejected connection with old security profile "
                f"{initial_security_profile}: {e}"
            )

        # Steps 12-13: Reconnect with NEW security profile again - must still be accepted.
        ws_final = await connect_with_profile(
            cp_id, new_security_profile,
            client_cert=new_client_cert, client_key=new_client_key,
        )
        time.sleep(0.5)
        assert ws_final.open, (
            f"CSMS should accept connection with upgraded security profile {new_security_profile}"
        )
        await ws_final.close()
    finally:
        # Restore original security profile so subsequent runs start clean
        await set_security_profile(cp_id, initial_security_profile)

        # Clean up temp certificate files from memory state
        if new_client_cert:
            os.unlink(new_client_cert)
        if new_client_key:
            os.unlink(new_client_key)
