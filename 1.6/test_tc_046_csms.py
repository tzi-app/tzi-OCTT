"""
Test case name      Reservation of a Connector - Transaction
Test case Id        TC_046_CSMS
OCPP Version        1.6J
Section             3.17.1 - Reservation of a Connector
Document ref        Table 166, Page 142/176 (CompliancyTestTool-TestCaseDocument 2025-11)

Description         A Connector is reserved and a charging transaction takes place.

Purpose             Check whether Central System can trigger a Charge Point to Reserve a Connector.

Prerequisite(s)     The Central System supports the Reservation feature profile.

Before:
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System sends a ReserveNow.req to the Charge Point.
2. The Charge Point responds with a ReserveNow.conf to the Central System.
3. The Charge Point sends a StatusNotification.req to the Central System.
4. The Central System responds with a StatusNotification.conf to the Charge Point.
5. Execute Reusable State: Charging
   (See Table 201 - Reusable State: Charging, which depends on Table 200 - Reusable State: Authorized.
    Full sub-flow:
      Authorized:
        a. CP sends Authorize.req (idTag: <Configured Valid IdTag>)
        b. CS responds with Authorize.conf (idTagInfo.status should be Accepted)
      Charging:
        c. CP sends StatusNotification.req (status: Preparing, connectorId: <Configured ConnectorId>)
        d. CS responds with StatusNotification.conf
        e. CP sends StartTransaction.req (idTag: <Configured Valid IdTag>,
           connectorId: <Configured ConnectorId>)
        f. CS responds with StartTransaction.conf (idTagInfo.status should be Accepted)
        g. CP sends StatusNotification.req (status: Charging, connectorId: <Configured ConnectorId>)
        h. CS responds with StatusNotification.conf)

Tool validations (Charge Point side):
* Step 2:
    Message: ReserveNow.conf
    - status is "Accepted"
* Step 3:
    Message: StatusNotification.req
    - status is "Reserved"
* Step 5:
    Reusable State: Charging
    - The reservationId is the reservationId from step 1

Tool validations (Central System side - SUT):
* Step 1:
    Message: ReserveNow.req
    - connectorId should be <Configured ConnectorId>
    - idTag should be <Configured Valid IdTag>

Expected result(s):    n/a (both sides per document)

NOTE (to be fixed later):
    - The document does not explicitly validate reservationId or expiryDate in the ReserveNow.req
      CS-side validations, but these are required fields per OCPP 1.6 spec. Confirm whether the
      OCTT tool validates them implicitly or if additional handling is needed.
    - Step 5 validation says "The reservationId is the reservationId from step 1" but it is unclear
      which specific message field this refers to (likely StartTransaction.req.reservationId).
"""
