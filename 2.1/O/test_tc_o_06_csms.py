"""
Test case name      Set Display Message - Specific transaction - Success
Test case Id        TC_O_06_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSO can set a message to be displayed on a Charging Station
                    for a specific transaction. Depending on the given parameters the message shall be
                    displayed a certain way on the Charging Station.

Purpose             To verify if the CSMS is able to send a display message correctly according the mechanism
                    as described in the OCPP specification for a specific transaction.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to send a display message for a specific transaction.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted
3. Execute Reusable State EVDisconnected

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.transactionId Same ID as previously returned by the Charging Station AND
    - message.priority <Configured Priority>

Post scenario validations:
    - N/a
"""
