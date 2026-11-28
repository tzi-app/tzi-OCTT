"""
Test case name      Certificate Installation EV - ISO 15118-20 - Success
Test case Id        TC_M_100_CSMS
Use case Id(s)      M01
Requirement(s)      M01.FR.02, M01.FR.05

Requirement Details:
    M01.FR.02 (2.1): Charging Station SHALL NOT include the field maximumContractCertificateChains in the
                     Get15118EVCertificateRequest message.
        Precondition: When EV uses ISO 15118-2
    M01.FR.05 (2.1): Charging station SHALL update the value of RemainingContractCertificateChains in the ISO
                     15118-20 CertificateInstallationRes message to EV to the value of remainingContracts of
                     the OCPP Get15118EVCertificateResponse message.
        Precondition: When EV uses ISO 15118-20 AND Upon receiving a Get15118EVCertificateResponse from CSMS
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
Note(s): 3 ContractCertificateChains will be communicated to the CSMS.

1. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
2. The CSMS responds with a Get15118EVCertificateResponse
3. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
4. The CSMS responds with a Get15118EVCertificateResponse
5. The Test System sends a Get15118EVCertificateRequest
    With action Install
    - maximumContractCertificateChains 10
    - prioritizedEMAIDs <Configured list EMA IDs>
6. The CSMS responds with a Get15118EVCertificateResponse

Tool validations
* Step 2:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 2
* Step 4:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 1
* Step 6:
    Message: Get15118EVCertificateResponse
    - status must be Accepted
    - exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
    - remainingContracts must be 0

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
# <Configured list EMA IDs>
CONFIGURED_PRIORITIZED_EMAIDS = os.environ['CONFIGURED_PRIORITIZED_EMAIDS'].split(',')

# The certificate provisioning service of the Test System, which the CSMS forwards to
CPS_PROXY_PORT = 19081
# The message definition of ISO 15118-20
ISO15118_20_SCHEMA_VERSION = 'urn:iso:std:iso:15118:-20:CommonMessages'


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_m_100(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    try:
        # Note(s): 3 ContractCertificateChains will be communicated to the CSMS.
        cps_proxy = MockCpsProxy(port=CPS_PROXY_PORT, contract_certificate_chains=3)
        cps_proxy.start()

        # 1. The Test System sends a Get15118EVCertificateRequest
        #    With action Install
        #    - maximumContractCertificateChains 10
        #    - prioritizedEMAIDs <Configured list EMA IDs>
        # 2. The CSMS responds with a Get15118EVCertificateResponse - remainingContracts must be 2
        # 3. The Test System sends the same Get15118EVCertificateRequest
        # 4. The CSMS responds with a Get15118EVCertificateResponse - remainingContracts must be 1
        # 5. The Test System sends the same Get15118EVCertificateRequest
        # 6. The CSMS responds with a Get15118EVCertificateResponse - remainingContracts must be 0
        for remaining_contracts in (2, 1, 0):
            response = await cp.send_get_15118_ev_certificate_request(
                iso15118_schema_version=ISO15118_20_SCHEMA_VERSION,
                action='Install',
                exi_request='dGVzdEVYSVJlcXVlc3REYXRh',
                maximum_contract_certificate_chains=10,
                prioritized_emaids=CONFIGURED_PRIORITIZED_EMAIDS,
            )
            assert response.status == 'Accepted', \
                f"Expected Get15118EVCertificateResponse.status Accepted, got {response.status}"
            # exiResponse <Raw CertificateInstallationRes response for the EV, Base64 encoded.>
            assert response.exi_response, "Get15118EVCertificateResponse has no exiResponse"
            assert response.remaining_contracts == remaining_contracts, \
                f"Expected Get15118EVCertificateResponse.remainingContracts {remaining_contracts}, " \
                f"got {response.remaining_contracts}"
    finally:
        cps_proxy.stop()

    start_task.cancel()
