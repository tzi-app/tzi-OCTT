"""
Reusable State      Charging
State Id            RS_CHARGING (editorial - not in official doc)
OCPP version        1.6J
System under test   Central System (CS)
Reference           Section 3.22, Table 201, document page 174/176
                    CompliancyTestTool-TestCaseDocument (PDF page 179)
                    CompliancyTestTool-TestCaseDocument-CSMS-Section3 (PDF pages 72-73)

Description         This state will simulate that the Charge Point starts a transaction.

Before (Preparations):
    Configuration State(s): N/a
    Memory State(s): N/a
    Reusable State(s):
        - Authorized

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
        - idTagInfo.status should be Accepted

Expected result(s) / behaviour:
    State is Charging.
"""
