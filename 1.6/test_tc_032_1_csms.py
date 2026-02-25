"""
Test case name      Power failure boot charging point-configured to stop transaction(s)
Test case Id        TC_032_1_CSMS
Profile             Core Profile - Power Failure Non-Happy Flow (Section 3.11)
Document ref        Table 149, Page 130/176 — Section 3.11.1
                    OCPP Compliancy Testing Tool - TestCaseDocument (2025-11)

Description         This scenario is used to stop all transactions, when a power failure occurred.
Purpose             To test if the Central System can handle when a Charge Point stops all transactions,
                    when a power failure occurred.

Prerequisite(s)     n/a

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): Charging
        (Reusable state "Charging" — Table 201, p.174 — simulates the CP starting a transaction.
         Depends on reusable state "Authorized". Sequence: StatusNotification(Preparing) →
         StartTransaction → StatusNotification(Charging). Validation: StartTransaction.conf
         idTagInfo.status should be Accepted.)

System under test   Central System (SUT)

Test Scenario
    [Disconnect and reconnect the power of the Charge Point.]
    1. The Charge Point sends a BootNotification.req
    2. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId = 0.]
    3. The Charge Point sends a StatusNotification.req
    4. The Central System responds with a StatusNotification.conf

    5. The Charge Point sends a StopTransaction.req
    6. The Central System responds with a StopTransaction.conf

Tool validation(s)
    Charge Point (Tool) side:
        * Step 3 - StatusNotification.req:
            - For the connector which had the ongoing transaction:
                connectorId = <the connector with the ongoing transaction>
                status = Finishing
            - For all other StatusNotification messages (including connectorId 0):
                status = Available

        * Step 5 - StopTransaction.req:
            - reason is PowerLoss

    Central System (SUT) side:
        * Step 2 - BootNotification.conf:
            - status is Accepted

Expected result(s) / behaviour
    n/a

Notes
    - The Charge Point must send StatusNotification for every connector AND for connectorId 0.
    - The connector that had the ongoing transaction reports Finishing; all others report Available.
    - The StopTransaction.req must include reason=PowerLoss to indicate the transaction was
      terminated due to a power failure.
    - This is OCPP 1.6J; messages use the 1.6 schema (BootNotification, StatusNotification,
      StopTransaction).
"""
