"""
Test case name      Retrieve specific configuration key
Test case Id        TC_019_2_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.2 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        Table 139, pages 124-125 (of 176), document version 2025-11

Description         The Central System is able to retrieve a specific configuration key.

Purpose             To check whether the Central System is able to retrieve a specific
                    Configuration key.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetConfiguration.req to the Charge Point
       with key = "SupportedFeatureProfiles".
    2. The Charge Point responds with a GetConfiguration.conf.

Tool Validations
    * Step 1 (GetConfiguration.req):
      - The key MUST be "SupportedFeatureProfiles".

    * Step 2 (GetConfiguration.conf):
      - The unknownKey list MUST be empty.
      - configurationKey.key MUST be "SupportedFeatureProfiles".
      NOTE: The official doc uses "should be" rather than "MUST" for the
      configurationKey.key validation. Treating as mandatory for test purposes.

Expected Result
    The Central System is able to retrieve the value of the requested
    configuration key.

OCPP 1.6 Messages
    GetConfiguration.req:
        - key (Optional, list of CiString50Type): List of keys for which the
          configuration value is requested. In this test, contains a single
          key: "SupportedFeatureProfiles".
    GetConfiguration.conf:
        - configurationKey (Optional, list of KeyValue): List of requested or
          available keys. Each KeyValue contains:
            - key (Required, CiString50Type): configuration key name
            - readonly (Required, boolean): whether the key is read-only
            - value (Optional, CiString500Type): current value of the key
        - unknownKey (Optional, list of CiString50Type): List of requested
          keys that are unknown to the Charge Point. Must be empty for this test.
"""
