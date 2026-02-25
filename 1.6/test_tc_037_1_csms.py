"""
Test case name      Offline Start Transaction - Valid IdTag
Test case Id        TC_037_1_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12. Core Profile - Offline behavior Non-Happy Flow
                    3.12.1. Offline Start Transaction - Valid IdTag
Document ref        Table 150 (Page 131/176)

Description         This scenario is used to start a transaction, while being offline.

Purpose             To test if the Central System can handle when a Charge Point starts a
                    transaction, while being offline and queues transaction-related messages,
                    after restoring the connection.

System under test   Central System (SUT)

Prerequisite(s)     n/a

Configuration State(s):
    n/a

Memory State(s):
    n/a

Reusable State(s):
    n/a

Test Scenario
    [Remove connectivity between Charge Point and Central System.]
    [EV Driver starts offline a transaction with a valid idTag.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req to the Central System.
    - connectorId: <Configured connectorId>
    - idTag: <Configured valid idTag>
    - meterStart: <meter value at transaction start>
    - timestamp: <timestamp of transaction start (while offline)>
2. The Central System responds with a StartTransaction.conf.
3. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Charging
4. The Central System responds with a StatusNotification.conf.

Tool validations
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Accepted
* Step 3:
    (Message: StatusNotification.req)
    status is Charging

Expected result(s)  n/a
"""
