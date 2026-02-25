"""
Test case name      Regular Charging Session - Plugin First
Test case Id        TC_003_CSMS
OCPP Version        1.6j
Chapter             3.2.1 - Start Charging Session
System under test   Central System
PDF Reference       CompliancyTestTool-TestCaseDocument-CSMS-Section3.pdf, pages 110-111, Table 123
HTML Reference      CompliancyTestTool-TestCaseDocument.html, page 110 of 176

Description         This scenario is used to start a Charging session.

Purpose             To test if the Central System can handle when the Charge Point starts a Charging
                    Session when first doing plugin cable.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
    Charge Point (Tool)                                     Central System (SUT)
    -----------------------------------------------         -----------------------------------------------
    [EV driver plugs in the cable.]
    1. The Charge Point sends a StatusNotification.req       2. The Central System responds with a
                                                                StatusNotification.conf

    [EV driver presents identification.]
    3. The Charge Point sends an Authorize.req               4. The Central System responds with an
                                                                Authorize.conf

    5. The Charge Point sends a StartTransaction.req         6. The Central System responds with a
                                                                StartTransaction.conf

    7. The Charge Point sends a StatusNotification.req       8. The Central System responds with a
                                                                StatusNotification.conf

Tool Validations
    * Step 1:
      (Message: StatusNotification.req)
      - status is Preparing

    * Step 4:
      (Message: Authorize.conf)
      - idTagInfo.status is Accepted

    * Step 6:
      (Message: StartTransaction.conf)
      - idTagInfo.status is Accepted

    * Step 7:
      (Message: StatusNotification.req)
      - status is Charging

Expected Result(s)  n/a
"""
