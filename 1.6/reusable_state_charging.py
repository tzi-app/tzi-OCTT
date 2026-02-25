"""
Reusable State      Charging
State Id            RS_CHARGING
OCPP version        1.6J
System under test   Central System (CS)
Reference           Table 201, page 174/176 (CompliancyTestTool-TestCaseDocument)

Description         This reusable state simulates that the Charge Point starts a transaction. It
                    transitions the connector through Preparing status, starts a transaction with
                    StartTransaction.req, and then transitions to Charging status. This state
                    depends on the Authorized reusable state being completed first.

Purpose             To bring the Charge Point into a known "Charging" state where an active transaction
                    is in progress on the configured connector.

Before (Preparations):
    Configuration State(s): N/a
    Memory State(s): N/a
    Reusable State(s):
        - Authorized (RS_AUTHORIZED must be executed first)

Scenario
1. The Charge Point sends a StatusNotification.req with:
   - status = Preparing
   - connectorId = <Configured ConnectorId>
2. The Central System responds with a StatusNotification.conf.
3. The Charge Point sends a StartTransaction.req with:
   - idTag = <Configured Valid IdTag>
   - connectorId = <Configured ConnectorId>
4. The Central System responds with a StartTransaction.conf.
5. The Charge Point sends a StatusNotification.req with:
   - status = Charging
   - connectorId = <Configured ConnectorId>
6. The Central System responds with a StatusNotification.conf.

Tool validations:
    * Step 4:
        (Message: StartTransaction.conf)
        - idTagInfo.status MUST be Accepted

Expected result(s) / behaviour:
    State is Charging.
    An active transaction is in progress on the configured connector. The connector
    status is Charging. The transaction was started with the previously authorized idTag.
"""
