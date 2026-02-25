"""
Reusable State      Booted
State Id            RS_BOOTED  [NOTE: "RS_BOOTED" is not in the document; doc only lists State = "Booted"]
OCPP version        1.6J
System under test   Central System (SUT)

Document ref        CompliancyTestTool-TestCaseDocument, Table 199, Section 3.22 "Reusable states", Page 173

Description         This state will simulate that the Charge Point is booting up.

Before (Preparations):
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario Detail(s)
    Charge Point (Tool)                         Central System (SUT)
    1. The Charge Point sends a                 2. The Central System responds with a
       BootNotification.req                        BootNotification.conf
       - chargePointVendor is
         <Configured Vendor Name>
       - chargePointModel is
         <Configured Model>

    [Send per connector and connectorId=0]
    3. The Charge Point sends a                 4. The Central System responds with a
       StatusNotification.req                      StatusNotification.conf
       - status is Available

Tool validation(s):
    * Step 2:
        (Message: BootNotification.conf)
        - status should be Accepted

Expected result(s) / behaviour:
    State is Booted
"""
