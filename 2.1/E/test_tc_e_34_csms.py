"""
Test case name      Check Transaction status - Without transactionId - without message in queue
Test case Id        TC_E_34_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.06, E14.FR.08

Requirement Details:
    E14.FR.06: The Charging Station’s response SHALL NOT have ongoingIndicator set.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId
    E14.FR.08: The Charging Station’s response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND
                      It has no transaction-related messages to be delivered
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages by sending a GetTransactionStatusRequest without a transactionId. The Test System
                    will respond that there are NO message(s) queued.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a GetTransactionStatusRequest
2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is omitted.
    messagesInQueue is false

Tool validations
* Step 1:
    Message: GetTransactionStatusRequest
    - transactionId must be omitted.

Post scenario validations:
    N/a
"""
