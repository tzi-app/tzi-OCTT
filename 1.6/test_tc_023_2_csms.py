"""
Test case name      Start Charging Session - Authorize expired
Test case Id        TC_023_2_CSMS
System under test   Central System
OCPP version        1.6J

Document Reference  CompliancyTestTool-TestCaseDocument, Section 3.8.2, Table 142, Page 126

Description         This scenario is used to inform the Charge Point that the EV Driver is not Authorized to start a
                    transaction.

Purpose             To test if the Central System is able to provide an expired response on an Authorize.req.

Prerequisite(s)     The Central System has an idTag in memory with status 'Expired'.

Before State(s)
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    [EV driver presents expired identification.]
    1. The Charge Point sends an Authorize.req
                                                2. The Central System responds with an
                                                   Authorize.conf

Tool validation(s)
    Charge Point (Tool): n/a
    Central System (SUT):
        * Step 1:
          (Message: Authorize.conf)
          idTagInfo.status is Expired

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Message Details (supplementary reference, not from test case document)
    Authorize.req:
        idTag (IdToken, max 20 chars): The identifier that needs to be authorized.
    Authorize.conf:
        idTagInfo (IdTagInfo):
            status (AuthorizationStatus): Accepted | Blocked | Expired | Invalid | ConcurrentTx
            expiryDate (optional, dateTime)
            parentIdTag (optional, IdToken)
"""
