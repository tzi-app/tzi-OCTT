"""
Test case name      Set Display Message - Specific transaction - UnknownTransaction
Test case Id        TC_O_10_CSMS
Use case Id(s)      O02
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how a CSMS can attempt to set a DisplayMessage for a
                    transactionId that the CS does not know. The CS will respond with a
                    SetDisplayMessageResponse status of UnknownTransaction.

Purpose             To verify if the CSMS is able to send a display message correctly according the mechanism
                    as described in the OCPP specification for a specific transaction.

Prerequisite(s)     If the CSMS supports sending a SetDisplayMessageRequest with a transactionId for a
                    transaction that does not exist.

Configuration State N/a

Memory State        N/a

Reusable State      State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to send a display message for a specific transaction.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with
    status UnknownTransaction

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.transactionId not omit AND
    - message.priority <Configured Priority>

Post scenario validations:
    - N/a
"""
