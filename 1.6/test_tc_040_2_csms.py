"""
Test case name      Configuration keys - Invalid value
Test case Id        TC_040_2_CSMS
OCPP version        1.6J
Profile             Core
Document ref        Section 3.13.2, Table 154, Page 134/176

System under test   Central System

Description         This scenario is used to reject setting a configuration key, when an incorrect
                    value is given.

Purpose             To test if the Central System is able to handle a Charge Point rejecting setting
                    a configuration key.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System (SUT) sends a ChangeConfiguration.req to the Charge Point (OCTT).
   - Message: ChangeConfiguration.req
   - Note: The tool only validates that key = MeterValueSampleInterval.
     The value to send is not specified by the test case document.
     (TODO: confirm what invalid value to use - the CS variant TC_040_2_CS uses -1)
2. The Charge Point (OCTT) responds with a ChangeConfiguration.conf.
   - Message: ChangeConfiguration.conf
   - Fields:
       status (ConfigurationStatus) - Rejected

Tool validations
* Step 1:
  (Message: ChangeConfiguration.req)
  The key MUST be MeterValueSampleInterval.
* Step 2:
  (Message: ChangeConfiguration.conf)
  The status MUST be Rejected.

Expected result(s) / behaviour
    Charge Point (Tool):    n/a
    Central System (SUT):   n/a

OCPP 1.6 Reference
    Section 5.3 - ChangeConfiguration
    ConfigurationStatus enum values: Accepted, Rejected, RebootRequired, NotSupported
    ChangeConfiguration.req is sent by the Central System to the Charge Point.
    ChangeConfiguration.conf is the Charge Point's response.
    MeterValueSampleInterval: interval (in seconds) between sampling of metering (or other) data.
"""
