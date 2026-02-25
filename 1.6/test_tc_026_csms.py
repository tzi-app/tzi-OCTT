"""
Test case name      Remote Start Charging Session – Rejected
Test case Id        TC_026_CSMS
OCPP Version        1.6J
Profile             Core
Chapter             3.9 Core Profile - Remote Actions Non-Happy Flow
Section             3.9.1
Document ref        Page 128/176, Table 145

System under test   Central System

Description         This scenario is used to reject a RemoteStartTransaction.req.

Purpose             To test if the Central System can handle when a Charge Point rejects a
                    RemoteStartTransaction.req.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      n/a

Test Scenario
1. The Central System (SUT) sends a RemoteStartTransaction.req to the Charge Point.
   [The CPO remotely requests a start transaction.]
   Note: The test case document does not specify required fields for this message.
         Per OCPP 1.6 spec, the request may contain:
       - idTag: an IdToken string (CiString20Type)
       - connectorId: (optional) Integer
       - chargingProfile: (optional) a ChargingProfile
2. The Charge Point (Tool) responds with a RemoteStartTransaction.conf.
   The response contains:
       - status: Rejected (RemoteStartStopStatus)

Tool validations
* Step 2:
    Message: RemoteStartTransaction.conf
    - status is Rejected

Expected result(s) / behaviour
    Charge Point (Tool): n/a
    Central System (SUT): n/a

Post scenario validations
    n/a

Implementation Notes
    - The OCTT acts as the Charge Point and must wait for the Central System (SUT) to initiate
      the RemoteStartTransaction.req.
    - Upon receiving the request, the OCTT responds with status=Rejected regardless of the
      idTag or connectorId provided.
    - The OCPP 1.6 RemoteStartTransaction is a Central System-initiated message
      (CSMS → CP direction), unlike BootNotification which is CP-initiated.
    - Message format (OCPP 1.6J JSON over WebSocket):
        RemoteStartTransaction.req:  [2, "<uniqueId>", "RemoteStartTransaction", {"idTag": "<string>"}]
        RemoteStartTransaction.conf: [3, "<uniqueId>", {"status": "Rejected"}]
"""
