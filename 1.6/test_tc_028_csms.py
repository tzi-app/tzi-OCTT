"""
Test case name      Remote Stop Transaction – Rejected
Test case Id        TC_028_CSMS
OCPP Version        1.6J
Profile             Core
Chapter             3.9 Core Profile - Remote Actions Non-Happy Flow
Section             3.9.2
Document Reference  Table 146, Page 128/176
                    (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

System under test   Central System

Description         This scenario is used to reject a RemoteStopTransaction.req, when an unknown
                    transactionId is given.

Purpose             To test if the Central System can handle when a Charge Point rejects a
                    RemoteStopTransaction.req, when an unknown transactionId is given.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s):        n/a
    Reusable State(s):      Charging
                            [TODO: "Charging" is a linked reusable state reference in the doc —
                             verify exact definition/preconditions from the Reusable States section]

Scenario Detail(s)
    Charge Point (Tool)                         Central System (SUT)
    2. The Charge Point responds with a         1. The Central System sends a
       RemoteStopTransaction.conf                  RemoteStopTransaction.req

Tool validation(s)
* Step 2:
    Message: RemoteStopTransaction.conf
    - status is Rejected

Expected result(s) / behaviour
    Charge Point (Tool):    n/a
    Central System (SUT):   n/a

Implementation Notes
    - The reusable state "Charging" means a transaction should be in progress before this
      test runs (the Charge Point is in a charging state). However, the Charge Point rejects
      the stop request because the transactionId in the request is unknown/does not match
      any active transaction.
    - The OCTT acts as the Charge Point and must wait for the Central System (SUT) to initiate
      the RemoteStopTransaction.req.
    - Upon receiving the request, the OCTT responds with status=Rejected to simulate that the
      given transactionId is not recognized.
    - The OCPP 1.6 RemoteStopTransaction is a Central System-initiated message
      (CSMS → CP direction).
    - Message format (OCPP 1.6J JSON over WebSocket):
        RemoteStopTransaction.req:  [2, "<uniqueId>", "RemoteStopTransaction", {"transactionId": <integer>}]
        RemoteStopTransaction.conf: [3, "<uniqueId>", {"status": "Rejected"}]
"""
