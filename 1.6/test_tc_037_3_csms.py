"""
Test case name      Offline Start Transaction - Invalid IdTag - StopTransactionOnInvalidId = true
Test case Id        TC_037_3_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12.2
Reference           CompliancyTestTool-TestCaseDocument, Page 131, Table 151

Description         This scenario is used to start a transaction, while being offline.

Purpose             To test if the Central System can handle when a Charge Point starts a transaction,
                    while being offline and queues transaction-related messages, after restoring the
                    connection.

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
    [EV Driver starts offline a transaction with an invalid idTag.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req to the Central System.
    - connectorId: <Configured connectorId>
    - idTag: <Configured invalid idTag>
    - meterStart: <meter value at transaction start>
    - timestamp: <timestamp of transaction start (while offline)>
2. The Central System responds with a StartTransaction.conf.
3. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Charging
4. The Central System responds with a StatusNotification.conf.
5. The Charge Point sends a StopTransaction.req to the Central System.
    - transactionId: <transactionId from Step 2>
    - reason: DeAuthorized
    - meterStop: <meter value at transaction stop>
    - timestamp: <timestamp of transaction stop>
6. The Central System responds with a StopTransaction.conf.
7. The Charge Point sends a StatusNotification.req to the Central System.
    - connectorId: <Configured connectorId>
    - errorCode: NoError
    - status: Finishing
8. The Central System responds with a StatusNotification.conf.

Tool validations
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Invalid
* Step 3:
    (Message: StatusNotification.req)
    status is Charging
* Step 5:
    (Message: StopTransaction.req)
    reason is DeAuthorized
* Step 7:
    (Message: StatusNotification.req)
    status is Finishing

Expected result(s) / behaviour
    n/a
"""
