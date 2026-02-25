"""
Test case name      Change/set Configuration
Test case Id        TC_021_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.3 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        Table 140, page 125 (CompliancyTestTool-TestCaseDocument)

Description         This scenario is used to set the value of a configuration key.

Purpose             To test if the Central System can handle when a Charge Point sets the
                    configuration key value, specified by the Central System.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a ChangeConfiguration.req to the Charge Point
       with key = "MeterValueSampleInterval" and value = "60".
    2. The Charge Point responds with a ChangeConfiguration.conf
       with status = "Accepted".

Tool Validations
    * Step 1 (ChangeConfiguration.req):
      - The key MUST be "MeterValueSampleInterval".
      - The value MUST be "60".

    * Step 2 (ChangeConfiguration.conf):
      - status MUST be "Accepted".

Expected Result
    Charge Point (Tool): n/a
    Central System (SUT): n/a

OCPP 1.6 Messages
    ChangeConfiguration.req:
        - key (Required, CiString50Type): The name of the configuration key
          to change. In this test: "MeterValueSampleInterval".
        - value (Required, CiString500Type): The new value for the
          configuration key. In this test: "60".
    ChangeConfiguration.conf:
        - status (Required, ConfigurationStatus): Returns whether the change
          was successful. Accepted values: Accepted, Rejected,
          RebootRequired, NotSupported.
"""
