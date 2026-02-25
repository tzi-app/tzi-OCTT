"""
Test case name      Retrieve all configuration keys
Test case Id        TC_019_1_CSMS
OCPP Version        1.6J
Profile             Core
Section             3.7.1 - Core Profile - Configuration Happy Flow
System under test   Central System (CSMS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 138, Pages 123-124/176

Description         The Central System is able to retrieve all available configuration keys.

Purpose             To check whether the Central System is able to retrieve all Configuration
                    keys and whether the Charge Point has all required keys configured.

Prerequisite(s)     n/a

Before              Configuration State(s): n/a
                    Memory State(s): n/a
                    Reusable State(s): n/a

Test Scenario
    1. The Central System sends a GetConfiguration.req to the Charge Point
       with an empty key list (no keys specified, meaning "get all").
    2. The Charge Point responds with a GetConfiguration.conf containing
       all available configuration keys.

Tool Validations
    * Step 1 (GetConfiguration.req):
      - The key list MUST be empty (no specific keys requested).

    * Step 2 (GetConfiguration.conf):
      - The response MUST contain all required configuration keys with correct
        accessibility (R = read-only, RW = read-write) as listed below.

      Core Profile Keys:
        - AuthorizeRemoteTxRequests / R or RW
        - ClockAlignedDataInterval / RW
        - ConnectionTimeOut / RW
        - ConnectorPhaseRotation / RW
        - GetConfigurationMaxKeys / R
        - HeartbeatInterval / RW
        - LocalAuthorizeOffline / RW
        - LocalPreAuthorize / RW
        - MeterValuesAlignedData / RW
        - MeterValuesSampledData / RW
        - MeterValueSampleInterval / RW
        - NumberOfConnectors / R
        - ResetRetries / RW
        - StopTransactionOnEVSideDisconnect / RW
        - StopTransactionOnInvalidId / RW
        - StopTxnAlignedData / RW
        - StopTxnSampledData / RW
        - SupportedFeatureProfiles / R
        - TransactionMessageAttempts / RW
        - TransactionMessageRetryInterval / RW
        - UnlockConnectorOnEVSideDisconnect / RW

      Local Auth List Management Keys:
        - LocalAuthListEnabled / RW
        - LocalAuthListMaxLength / R
        - SendLocalListMaxLength / R

      Smart Charging Profile Keys:
        - ChargeProfileMaxStackLevel / R
        - ChargingScheduleAllowedChargingRateUnit / R
        - ChargingScheduleMaxPeriods / R
        - MaxChargingProfilesInstalled / R

      Reservation Profile Keys:
        - None

      Remote Trigger Profile Keys:
        - None

Expected Result
    All required keys are configured. The Central System is able to retrieve
    the values of all requested configuration keys.

OCPP 1.6 Messages
    GetConfiguration.req:
        - key (Optional, list of CiString50Type): List of keys for which the
          configuration value is requested. When empty, all configuration keys
          are returned.
    GetConfiguration.conf:
        - configurationKey (Optional, list of KeyValue): List of requested or
          available keys. Each KeyValue contains:
            - key (Required, CiString50Type): configuration key name
            - readonly (Required, boolean): whether the key is read-only
            - value (Optional, CiString500Type): current value of the key
        - unknownKey (Optional, list of CiString50Type): List of requested
          keys that are unknown to the Charge Point.
"""
