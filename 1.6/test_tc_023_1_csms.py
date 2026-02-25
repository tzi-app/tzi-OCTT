"""
Test case name      Start Charging Session - Authorize invalid
Test case Id        TC_023_1_CSMS
System under test   Central System
OCPP version        1.6J
Document ref        Page 126/176, Section 3.8.1, Table 141

Description         This scenario is used to inform the Charge Point that the EV Driver is not Authorized to start a
                    transaction.

Purpose             To test if the Central System is able to provide an invalid response on an Authorize.req.

Prerequisite(s)     n/a

Before State(s)
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. [EV driver presents invalid identification.]
   The Charge Point sends an Authorize.req to the Central System.
   - Message: Authorize.req
2. The Central System responds with an Authorize.conf.
   - Message: Authorize.conf

Tool validation(s)
* Step 1:
    (Message: Authorize.conf)
    - idTagInfo.status is Invalid
"""
