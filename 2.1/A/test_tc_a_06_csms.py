"""
Test case name      TLS - server-side certificate - TLS version too low
Test case Id        TC_A_06_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.314, A00.FR.315, A00.FR.409, A00.FR.416, A00.FR.417, A00.FR.418

Requirement Details:
    A00.FR.314: Both of these endpoints SHALL check the version of TLS used.
    A00.FR.315: The CSMS SHALL terminate the connection.
        Precondition: A00.FR.314 AND The CSMS detects that the Charging Station only allows connections using
                      an older version of TLS, or only allows SSL
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.416: The Charging Station and CSMS SHALL only use TLS v1.2 or above. (Same as A00.FR.313)
    A00.FR.417: Both of these endpoints SHALL check the version of TLS used. (Same as A00.FR.314)
    A00.FR.418: The CSMS SHALL terminate the connection. (Same as A00.FR.315)
        Precondition: A00.FR.417 AND The CSMS detects that the Charging Station only allows connections using
                      an older version of TLS, or only allows SSL
System under test   CSMS

Description         The CSMS uses a server-side certificate to identify itself to the Charging Station, when
                    using security profile 2 or 3.

Purpose             To verify whether the CSMS is able to terminate the connection when it notices the used
                    TLS version is lower than 1.2.

Prerequisite(s)     The CSMS supports security profile 2 and/or 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System terminates the connection and initiates a TLS handshake with a TLS version lower than 1.2
   and sends a Client Hello to the CSMS.
2. The CSMS notices that the TLS version is lower than 1.2 and terminates the connection.
3. The Test System initiates a TLS handshake with TLS version 1.2 or higher and sends a Client Hello to the
   CSMS.
4. The CSMS responds with a Server Hello
    With the <Configured server certificate>
5. The Test System performs the following actions:
    Send client certificate
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
    Note(s):
    - The client certificate is only sent when the CSMS uses security profile 3.
6. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
7. The Test System sends a HTTP upgrade request to the CSMS
    Note(s):
    - The HTTP request only contains a username/password combination when the CSMS uses security profile 2.
8. The CSMS upgrades the connection to a (secured) WebSocket connection.
9. The Test System sends a BootNotificationRequest
    with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
10. The CSMS responds with a BootNotificationResponse
11. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
12. The CSMS responds accordingly.

Tool validations
* Step 10:
    Message: BootNotificationResponse
    - status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.3. Page 24 - (2026-02) - A00.FR.308 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        |  | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. |  |
        | New | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] |  |

    2.4. Page 26 - (2026-02) - A00.FR.403 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] | |
        | New | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] | |

    2.6. Page 27 - (2026-02) - A00.FR.411 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. (Same as
          A00.FR.308) | |
        | New | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26]. (Same as A00.FR.308) | |
"""

import asyncio
import logging
import os
import ssl

import pytest

from charge_point import TziChargePoint21, connect_to_csms
from security import connect_with_profile, headers_for, ssl_context_for

SECURITY_PROFILE_2_CP = os.environ['CP21_SP2']
SECURITY_PROFILE_3_CP = os.environ['CP21_SP3']


@pytest.mark.asyncio
@pytest.mark.parametrize("security_profile", [2, 3])
async def test_tc_a_06(security_profile):
    cp_id = SECURITY_PROFILE_2_CP if security_profile == 2 else SECURITY_PROFILE_3_CP

    # 1. The Test System initiates a TLS handshake with a TLS version lower than 1.2 and sends
    #    a Client Hello to the CSMS.
    # 2. The CSMS notices that the TLS version is lower than 1.2 and terminates the connection.
    #
    # The client has to be able to offer such a version. Python sets TLS 1.2 as the minimum
    # version, and OpenSSL 3 disables TLS 1.0 and 1.1 above security level 0. Without the
    # settings below, the handshake fails in the client, before a Client Hello reaches the
    # CSMS.
    low_tls_ctx = ssl_context_for(security_profile)
    low_tls_ctx.check_hostname = False
    low_tls_ctx.verify_mode = ssl.CERT_NONE
    low_tls_ctx.minimum_version = ssl.TLSVersion.TLSv1
    low_tls_ctx.maximum_version = ssl.TLSVersion.TLSv1_1
    low_tls_ctx.set_ciphers('DEFAULT:@SECLEVEL=0')

    with pytest.raises((ssl.SSLError, ConnectionError)) as terminated:
        ws = await connect_to_csms(
            cp_id, headers=headers_for(cp_id, security_profile), ssl_context=low_tls_ctx)
        await ws.close()

    # Check that the CSMS terminated the connection, and that the client did not give up before
    # sending its Client Hello.
    assert getattr(terminated.value, 'reason', None) != 'NO_PROTOCOLS_AVAILABLE', \
        f"The client could not offer a TLS version lower than 1.2: {terminated.value}"
    logging.info(f"CSMS terminated the TLS < 1.2 handshake: {terminated.value}")

    # 3-6. TLS handshake with TLS version 1.2 or higher. The client certificate is only sent
    #      when the CSMS uses security profile 3.
    # 7.   The Test System sends a HTTP upgrade request to the CSMS. It only contains a
    #      username/password combination when the CSMS uses security profile 2.
    # 8.   The CSMS upgrades the connection to a (secured) WebSocket connection.
    ws = await connect_with_profile(cp_id, security_profile)
    try:
        cp = TziChargePoint21(cp_id, ws)
        start_task = asyncio.create_task(cp.start())

        # 9.  The Test System sends a BootNotificationRequest with reason PowerUp, the
        #     configured model and the configured vendorName
        # 10. The CSMS responds with a BootNotificationResponse with status Accepted
        boot_response = await cp.send_boot_notification(reason='PowerUp')
        assert boot_response.status == 'Accepted', \
            f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

        # 11. The Test System notifies the CSMS about the current state of all connectors.
        #     StatusNotificationRequest - connectorStatus Available
        #     NotifyEventRequest - trigger Delta, actualValue "Available",
        #                          component.name "Connector", variable.name "AvailabilityState"
        # 12. The CSMS responds accordingly.
        await cp.send_all_connectors_status('Available')

        start_task.cancel()
    finally:
        await ws.close()
