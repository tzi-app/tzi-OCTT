"""
Test case name      Start Charging Session – Authorize blocked
Test case Id        TC_023_3_CSMS
System under test   Central System
OCPP version        1.6J

Document ref        OCPP Compliancy Testing Tool - TestCaseDocument (2025-11)
                    Section 3.8.3, Table 143, Page 127/176

Description         This scenario is used to inform the Charge Point that the EV Driver is not Authorized to start a
                    transaction. The Charge Point sends an Authorize.req with an idTag that the Central System recognizes
                    but has marked as blocked.

Purpose             To test if the Central System is able to provide a blocked response on an Authorize.req.

Prerequisite(s)     - The Central System has an idTag in memory with status 'Blocked'.

Before State(s)
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. [EV driver presents blocked identification.]
   The Charge Point sends an Authorize.req to the Central System.
   - Message: Authorize.req
   - idTag: An idTag value that is known at the Central System but has status 'Blocked'
2. The Central System responds with an Authorize.conf.
   - Message: Authorize.conf

Tool validations (Central System)
* Step 2:
    (Message: Authorize.conf)
    - idTagInfo.status MUST be "Blocked"
    NOTE: The official document labels this as "Step 1" in the CS column, but the
          Authorize.conf is scenario step 2. Possible document numbering discrepancy.

Tool validations (Charge Point)
    n/a

Expected result(s) / behaviour
    Charge Point (Tool):    n/a
    Central System (SUT):   n/a

OCPP 1.6 Message Details
    Authorize.req:
        idTag (IdToken, max 20 chars): The identifier that needs to be authorized.
    Authorize.conf:
        idTagInfo (IdTagInfo):
            status (AuthorizationStatus): Accepted | Blocked | Expired | Invalid | ConcurrentTx
            expiryDate (optional, dateTime)
            parentIdTag (optional, IdToken)
"""
