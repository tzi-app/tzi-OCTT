"""
Test case name      Regular Start Charging Session – Cached Id
Test case Id        TC_007_CSMS
OCPP version        1.6J
Chapter             3.3 Cache (3.3.1)
Doc reference       CompliancyTestTool-TestCaseDocument, Table 127, Section 3.3.1, p.113

System under test   Central System

Description         This scenario is used to start a transaction with an id stored in the Authorization cache.

Purpose             To test if the Central System is able to handle a Charge Point starting a transaction with an id
                    which is stored in the Authorization cache.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    [EV driver plugs in the cable.]
    1. The Charge Point sends a StatusNotification.req to the Central System with status=Preparing,
       connectorId=1, errorCode=NoError.
    2. The Central System responds with a StatusNotification.conf.
    [EV driver presents identification.]
    3. The Charge Point sends a StartTransaction.req to the Central System with connectorId=1,
       idTag=<cached_id_tag>, meterStart=0, timestamp=<current_timestamp>.
       The idTag used MUST be one that is present in the Charge Point's Authorization cache.
    4. The Central System responds with a StartTransaction.conf containing idTagInfo.status=Accepted
       and a transactionId.
    5. The Charge Point sends a StatusNotification.req to the Central System with status=Charging,
       connectorId=1, errorCode=NoError.
    6. The Central System responds with a StatusNotification.conf.

Tool validation(s)
    * Step 1:
        (Message: StatusNotification.req)
        - status is Preparing
    * Step 4:
        (Message: StartTransaction.conf)
        - idTagInfo.status is Accepted
    * Step 5:
        (Message: StatusNotification.req)
        - status is Charging

Expected result(s) n/a

Post scenario validations:
    n/a
"""
