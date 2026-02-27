"""
Test case name      Regular Charging Session – Identification First
Test case Id        TC_004_1_CSMS
OCPP Version        1.6j
Section             3.2.2 - Regular Charging Session – Identification First
System under test   Central System (CSMS)

Document Reference  OCTT Test Case Document (2025-11), Table 124, Section 3.2.2, Page 111/176

Description         This scenario is used to start a charging session.
                    (The official CSMS test case description is just the single sentence above.
                    Context: the EV driver first presents identification, is authorized, and then
                    plugs in the cable. This is the "Identification First" variant — the reverse
                    order of TC_003 "Plugin First".)

Purpose             To test if the Central System can handle when the Charge Point starts a
                    charging session when first doing authorization.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Scenario
    The official test case scenario is:
        - Execute Reusable State "Charging" (Table 201, Page 174/176)
    The Charging reusable state in turn requires:
        - Execute Reusable State "Authorized" (Table 200, Page 173/176)

    Expanded scenario (from reusable states):

    --- Reusable State: Authorized (Table 200) ---
    Description: "This state will simulate that the EV Driver is locally
    authorizing to start a transaction on the simulated Charge Point."
    1. The Charge Point sends an Authorize.req to the Central System.
       - idTag = <Configured Valid IdTag>
    2. The Central System responds with an Authorize.conf.

    --- Reusable State: Charging (Table 201) ---
    Description: "This state will simulate that the Charge Point starts a transaction."
    Before: Reusable State(s): Authorized
    3. The Charge Point sends a StatusNotification.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - status = Preparing
    4. The Central System responds with a StatusNotification.conf.
    5. The Charge Point sends a StartTransaction.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - idTag = <Configured Valid IdTag>
    6. The Central System responds with a StartTransaction.conf.
    7. The Charge Point sends a StatusNotification.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - status = Charging
    8. The Central System responds with a StatusNotification.conf.

Tool Validations (TC_004_1 itself has no tool validations; all come from reusable states)
    From Authorized state (Table 200):
        Step 2 (Central System -> Charge Point):
            Message: Authorize.conf
            - idTagInfo.status should be Accepted

    From Charging state (Table 201):
        Step 4 (Central System -> Charge Point):
            Message: StartTransaction.conf
            - idTagInfo.status should be Accepted

Expected Result(s)  n/a (per official document)
                    (The Charging reusable state expects: "State is Charging")

OCPP 1.6 Messages Used:
    - Authorize.req / Authorize.conf
    - StatusNotification.req / StatusNotification.conf
    - StartTransaction.req / StartTransaction.conf

Key Fields (from OCPP 1.6 spec, for implementation reference):
    Authorize.req:
        - idTag (IdToken, required, String max 20 chars - the identifier to authorize)

    Authorize.conf:
        - idTagInfo (IdTagInfo, required):
            - status (AuthorizationStatus: Accepted | Blocked | Expired | Invalid |
                      ConcurrentTx)
            - expiryDate (dateTime, optional)
            - parentIdTag (IdToken, optional)

    StatusNotification.req:
        - connectorId (Integer, required, >= 0; 0 = Charge Point main controller)
        - errorCode (ChargePointErrorCode, required; e.g. NoError)
        - status (ChargePointStatus: Available | Preparing | Charging | SuspendedEVSE |
                  SuspendedEV | Finishing | Reserved | Unavailable | Faulted)
        - timestamp (dateTime, optional)

    StatusNotification.conf:
        - (empty payload)

    StartTransaction.req:
        - connectorId (Integer, required, > 0)
        - idTag (IdToken, required, String max 20 chars)
        - meterStart (Integer, required, Wh meter value at start)
        - timestamp (dateTime, required)
        - reservationId (Integer, optional)

    StartTransaction.conf:
        - transactionId (Integer, required - assigned by Central System)
        - idTagInfo (IdTagInfo, required):
            - status (AuthorizationStatus: Accepted | Blocked | Expired | Invalid |
                      ConcurrentTx)
            - expiryDate (dateTime, optional)
            - parentIdTag (IdToken, optional)
"""

import asyncio
import os
import pytest

from charge_point import TziChargePoint16
from reusable_states import authorized, charging
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['BASIC_AUTH_CP']
TEST_USER_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
VALID_ID_TAG = os.environ['VALID_ID_TOKEN']
CONNECTOR_ID = int(os.environ.get('CONFIGURED_CONNECTOR_ID', '1'))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, TEST_USER_PASSWORD))],
                         indirect=True)
async def test_tc_004_1(connection):
    assert connection.open
    cp = TziChargePoint16(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())

    # Reusable State: Authorized (Table 200)
    await authorized(cp, VALID_ID_TAG)

    # Reusable State: Charging (Table 201)
    start_response, transaction_id = await charging(cp, VALID_ID_TAG, CONNECTOR_ID)
    assert transaction_id is not None

    start_task.cancel()
