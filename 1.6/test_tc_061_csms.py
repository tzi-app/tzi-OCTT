"""
Test case name      Clear Authorization Data in Authorization Cache
Test case Id        TC_061_CSMS
OCPP version        1.6J
Chapter             3.3.2 Clear Authorization Data in Authorization Cache
Document ref        CompliancyTestTool-TestCaseDocument, Table 128, pages 113-114/176

System under test   Central System

Description         The Central System can clear the Authorization Cache of a Charge Point.

Purpose             Check whether the Central System can clear the Authorization Cache of a Charge Point.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. [CS → CP] The Central System sends a ClearCache.req.
    2. [CP → CS] The Charge Point responds with a ClearCache.conf.

Tool validation(s)
    * Step 2:
        (Message: ClearCache.conf)
        - status is Accepted

Expected result(s)
    - [CP] The Charge Point Authorization Cache is cleared.
    - [CS] The Central System is able to send a message to clear the cache.

Post scenario validations:
    n/a
"""
