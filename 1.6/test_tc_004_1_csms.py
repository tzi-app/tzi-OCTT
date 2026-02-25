"""
Test case name      Regular Charging Session – Identification First
Test case Id        TC_004_1_CSMS
OCPP Version        1.6j
Section             3.2.2 - Regular Charging Session – Identification First
System under test   Central System (CSMS)

Document Reference  OCTT Test Case Document (2025-11), Table 124, Section 3.2.2, Page 111/176

Description         This scenario is used to start a charging session.
                    (The official CSMS test case description is just the single sentence above.
                    Context: the EV driver first presents identification, is authorized, and then
                    plugs in the cable. This is the "Identification First" variant — the reverse
                    order of TC_003 "Plugin First".)

Purpose             To test if the Central System can handle when the Charge Point starts a
                    charging session when first doing authorization.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Scenario
    The official test case scenario is:
        - Execute Reusable State "Charging" (Table 201, Page 174/176)
    The Charging reusable state in turn requires:
        - Execute Reusable State "Authorized" (Table 200, Page 173/176)

    Expanded scenario (from reusable states):

    --- Reusable State: Authorized (Table 200) ---
    1. The Charge Point sends an Authorize.req to the Central System.
       - idTag = <Configured Valid IdTag>
    2. The Central System responds with an Authorize.conf.

    --- Reusable State: Charging (Table 201) ---
    3. The Charge Point sends a StatusNotification.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - status = Preparing
    4. The Central System responds with a StatusNotification.conf.
    5. The Charge Point sends a StartTransaction.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - idTag = <Configured Valid IdTag>
    6. The Central System responds with a StartTransaction.conf.
    7. The Charge Point sends a StatusNotification.req to the Central System.
       - connectorId = <Configured ConnectorId>
       - status = Charging
    8. The Central System responds with a StatusNotification.conf.

    NOTE: The official CSMS scenario does not include physical actions like
    "[EV driver presents identification]" or "[EV driver plugs in cable]" — those
    appear in the CS (Charge Point SUT) version (TC_004_1_CS, Table 4). The OCTT
    tool simulates the Charge Point and drives these actions automatically.

    NOTE: The official reusable states use "<Configured ConnectorId>" and
    "<Configured Valid IdTag>" — the actual values come from OCTT configuration.

    NOTE: The official Charging reusable state does not explicitly list errorCode,
    meterStart, timestamp, or transactionId fields in the scenario steps. These
    are implicit per the OCPP 1.6 message definitions.

Tool Validations (from reusable states)
    From Authorized state (Table 200):
        Step 2 (Central System -> Charge Point):
            Message: Authorize.conf
            - idTagInfo.status SHOULD be "Accepted"

    From Charging state (Table 201):
        Step 6 (Central System -> Charge Point):
            Message: StartTransaction.conf
            - idTagInfo.status SHOULD be "Accepted"

    NOTE: The official CSMS test case itself has no tool validations (n/a).
    The validations above come from the reusable state definitions. The official
    wording uses "should be" (not "MUST be"). The CS version (TC_004_1_CS)
    additionally validates StatusNotification.req status for Preparing and
    Charging — those are NOT present in the CSMS reusable states.

Expected Result(s)  n/a (per official document)
                    (The Charging reusable state expects: "State is Charging")

OCPP 1.6 Messages Used:
    - Authorize.req / Authorize.conf
    - StatusNotification.req / StatusNotification.conf
    - StartTransaction.req / StartTransaction.conf

Key Fields (from OCPP 1.6 spec, for implementation reference):
    Authorize.req:
        - idTag (IdToken, required, String max 20 chars - the identifier to authorize)

    Authorize.conf:
        - idTagInfo (IdTagInfo, required):
            - status (AuthorizationStatus: Accepted | Blocked | Expired | Invalid |
                      ConcurrentTx)
            - expiryDate (dateTime, optional)
            - parentIdTag (IdToken, optional)

    StatusNotification.req:
        - connectorId (Integer, required, >= 0; 0 = Charge Point main controller)
        - errorCode (ChargePointErrorCode, required; e.g. NoError)
        - status (ChargePointStatus: Available | Preparing | Charging | SuspendedEVSE |
                  SuspendedEV | Finishing | Reserved | Unavailable | Faulted)
        - timestamp (dateTime, optional)

    StatusNotification.conf:
        - (empty payload)

    StartTransaction.req:
        - connectorId (Integer, required, > 0)
        - idTag (IdToken, required, String max 20 chars)
        - meterStart (Integer, required, Wh meter value at start)
        - timestamp (dateTime, required)
        - reservationId (Integer, optional)

    StartTransaction.conf:
        - transactionId (Integer, required - assigned by Central System)
        - idTagInfo (IdTagInfo, required):
            - status (AuthorizationStatus: Accepted | Blocked | Expired | Invalid |
                      ConcurrentTx)
            - expiryDate (dateTime, optional)
            - parentIdTag (IdToken, optional)
"""
