"""
Test case name      Certificate Installation EV - Success
Test case Id        TC_M_26_CSMS
Use case Id(s)      M01
Requirement(s)      M01.FR.01

Requirement Details:
    M01.FR.01: The Charging Station SHALL forward the request to the CSMS using the
               Get15118EVCertificateRequest message with action = Install.
        Precondition: Upon receiving an ISO 15118 CertificateInstallationReq
        Note: The CSMS is responsible for forwarding it to the secondary actor which will process the
              CertificateUpdateRequest. This could be a contract certificate pool as outlined in application
              guide VDE-AR-2802-100-1.
System under test   CSMS

Description         The EV initiates installing a new certificate. The Charging Station forwards the request
                    for a new certificate to the CSMS.

Purpose             To verify if the CSMS is able to return the Raw CertificateInstallationRes response for
                    the EV to the Charging Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a Get15118EVCertificateRequest
    With action Install
2. The CSMS responds with a Get15118EVCertificateResponse

Tool validations
* Step 2:
    Message: Get15118EVCertificateResponse
    - status Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.16. Page 1264/1265/1266 - (2026-09) - TC_M_100_CSMS / TC_M_26_CSMS / TC_M_28_CSMS - Included
        iso15118SchemaVersion information
        | Test case name | Certificate Installation EV - ISO 15118-20 - Success |
        | Test case Id | TC_M_100_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Note(s): 3 ContractCertificateChains will be communicated to the CSMS. | |

        | Test case Id | TC_M_26_CSMS / TC_M_28_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends a Get15118EVCertificateRequest / With action Update / iso15118SchemaVersion
          urn:iso:15118:2:2013:MsgDef | 2. The CSMS responds with a Get15118EVCertificateResponse |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from mock_cps_proxy import MockCpsProxy
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# The certificate provisioning service of the Test System, which the CSMS forwards to
CPS_PROXY_PORT = 19081


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_26(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    try:
        cps_proxy = MockCpsProxy(port=CPS_PROXY_PORT)
        cps_proxy.start()

        # 1. The Test System sends a Get15118EVCertificateRequest
        #    With action Install
        #    iso15118SchemaVersion urn:iso:15118:2:2013:MsgDef (errata 2026-09, 6.3.16)
        # 2. The CSMS responds with a Get15118EVCertificateResponse
        response = await cp.send_get_15118_ev_certificate_request(
            iso15118_schema_version='urn:iso:15118:2:2013:MsgDef',
            action='Install',
            exi_request='dGVzdEVYSVJlcXVlc3REYXRh',
        )
        assert response.status == 'Accepted', \
            f"Expected Get15118EVCertificateResponse.status Accepted, got {response.status}"
        # exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
        assert response.exi_response, "Get15118EVCertificateResponse has no exiResponse"
    finally:
        cps_proxy.stop()

    start_task.cancel()
