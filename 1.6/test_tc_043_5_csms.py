"""
Test case name      Send Local Authorization List - Differential
Test case Id        TC_043_5_CSMS
System under test   Central System
Document ref        Section 3.14.2, Table 160, pages 137-138/176
                    (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             Check whether a Local Authorization List can be sent to a Charge Point to
                    authorize an EV driver.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile and
                    has at least 1 IdToken to add to the local authorization list.

Before
    Configuration State(s): n/a
    Memory State(s):
        Set the initial local authorization list using update type full.
    Reusable State(s): n/a

Test Scenario
1. The Central System sends a GetLocalListVersion.req to the Charge Point.
2. The Charge Point responds with a GetLocalListVersion.conf.
   (Note: Messages 1 and 2 are optional.)
   Manual Action: Trigger the Central System to send a SendLocalList updateType Differential
   for a specific idToken that is not already part of the list.
3. The Central System sends a SendLocalList.req.
4. The Charge Point responds with a SendLocalList.conf.

Tool validations
    * Step 2: (Message: GetLocalListVersion.conf)
        - listVersion is <Provided listVersion by Central System>.
    * Step 3: (Message: SendLocalList.req)
        - updateType should be Differential.
        - localAuthorizationList contains <Only the specified idToken, including an idTagInfo.>
        - versionNumber should be <Greater than the initial listVersion.>
    * Step 4: (Message: SendLocalList.conf)
        - status is Accepted.

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a
"""
