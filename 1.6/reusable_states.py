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
    """Reusable State: Booted
    Document ref: Section 3.22, Table 199, Page 173
                  CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11)

    Description:  This state will simulate that the Charge Point is booting up.

    Before (Preparations):
        Configuration State(s): n/a
        Memory State(s):        n/a
        Reusable State(s):      n/a

    Scenario:
        1. CP sends BootNotification.req
           - chargePointVendor = <Configured Vendor Name>
           - chargePointModel  = <Configured Model>
        2. CS responds with BootNotification.conf
        [Send per connector and connectorId=0]
        3. CP sends StatusNotification.req  (status = Available)
        4. CS responds with StatusNotification.conf

    Tool validation(s):
        * Step 2 (BootNotification.conf): status should be Accepted

    Expected result: State is Booted

    Returns the boot_response.
    """
    boot_response = await cp.send_boot_notification()
    assert boot_response.status == RegistrationStatus.accepted

    for connector_id in (0, 1):
        await cp.send_status_notification(connector_id, status=ChargePointStatus.available)

    return boot_response


async def authorized(cp, id_tag):
    """Reusable State: Authorized
    Document ref: Section 3.22, Table 200, Pages 173-174
                  CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11)

    Description:  This state will simulate that the EV Driver is locally authorizing
                  to start a transaction on the simulated Charge Point.

    Before (Preparations):
        Configuration State(s): n/a
        Memory State(s):        n/a
        Reusable State(s):      n/a

    Scenario:
        1. CP sends Authorize.req
           - idTag = <Configured Valid IdTag>
        2. CS responds with Authorize.conf

    Tool validation(s):
        * Step 2 (Authorize.conf): idTagInfo.status should be Accepted

    Expected result: State is Authorized

    Returns the authorize_response.
    """
    auth_response = await cp.send_authorize(id_tag)
    assert auth_response.id_tag_info['status'] == AuthorizationStatus.accepted
    return auth_response


async def charging(cp, id_tag, connector_id=1):
    """Reusable State: Charging
    Document ref: Section 3.22, Table 201, Page 174
                  CompliancyTestTool-TestCaseDocument-CSMS-Section3 (2025-11)

    Description:  This state will simulate that the Charge Point starts a transaction.

    Before (Preparations):
        Configuration State(s): n/a
        Memory State(s):        n/a
        Reusable State(s):      Authorized

    Scenario:
        1. CP sends StatusNotification.req
           - status      = Preparing
           - connectorId = <Configured ConnectorId>
        2. CS responds with StatusNotification.conf
        3. CP sends StartTransaction.req
           - idTag       = <Configured Valid IdTag>
           - connectorId = <Configured ConnectorId>
        4. CS responds with StartTransaction.conf
        5. CP sends StatusNotification.req
           - status      = Charging
           - connectorId = <Configured ConnectorId>
        6. CS responds with StatusNotification.conf

    Tool validation(s):
        * Step 4 (StartTransaction.conf): idTagInfo.status should be Accepted

    Expected result: State is Charging

    Returns (start_response, transaction_id).
    """
    await cp.send_status_notification(connector_id, status=ChargePointStatus.preparing)

    start_response = await cp.send_start_transaction(connector_id, id_tag)
    assert start_response.id_tag_info['status'] == AuthorizationStatus.accepted
    transaction_id = start_response.transaction_id

    await cp.send_status_notification(connector_id, status=ChargePointStatus.charging)

    return start_response, transaction_id
