"""
Test case name      Offline Transaction
Test case Id        TC_039_CSMS
OCPP version        1.6J
Profile             Core
Section             3.12.3
Table               152
Document page       132-133/176

Description         This scenario is used to start and stop a transaction, while the Charge
                    Point is offline.

Purpose             To test if the Central System is able to handle queued transaction-related
                    messages, after a Charge Point comes back online again.

System under test   Central System (SUT)

Prerequisite(s)     Before: n/a

Configuration State(s):
    n/a

Memory State(s):
    n/a

Reusable State(s):
    n/a

Test Scenario
    [Remove connectivity between Charge Point and Central System.]
    [EV Driver starts offline a transaction.]
    [EV Driver stops offline a transaction.]
    [EV driver unplugs the cable.]
    [Restore connectivity between Charge Point and Central System.]

1. The Charge Point sends a StartTransaction.req
2. The Central System responds with a StartTransaction.conf
3. The Charge Point sends a StopTransaction.req
4. The Central System responds with a StopTransaction.conf

    NOTE: The official test case document does not include field-level details for the
    steps above. The following fields are inferred from the OCPP 1.6 specification and
    may be sent by the OCTT tool (to be verified):
    - Step 1: connectorId, idTag, meterStart, timestamp
    - Step 3: transactionId (from Step 2), reason=Local, meterStop, timestamp

Tool validations
* Step 2:
    (Message: StartTransaction.conf)
    idTagInfo.status is Accepted
* Step 3:
    (Message: StopTransaction.req)
    reason is Local

Expected result(s) / behaviour
    n/a
"""
