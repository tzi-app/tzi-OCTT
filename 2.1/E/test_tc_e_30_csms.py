"""
Test case name      Check Transaction status - Transaction with id ongoing - without message in queue
Test case Id        TC_E_30_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.02, E14.FR.05

Requirement Details:
    E14.FR.02: The Charging Station’s response SHALL have ongoingIndicator = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has not stopped yet
    E14.FR.05: The Charging Station’s response SHALL have messagesInQueue = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It
                      has no transaction-related messages to be delivered about the transaction with that
                      transactionId
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages from a specific transaction by sending a GetTransactionStatusRequest with a
                    transactionId. The Test System will respond that there is NO message queued belonging to
                    the ongoing transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The CSMS sends a GetTransactionStatusRequest
2. The Test System responds with a GetTransactionStatusResponse With ongoingIndicator is true
    messagesInQueue is false

Tool validations
* Step 1:
    Message: GetTransactionStatusRequest
    - transactionId must be <Generated transactionId from Before>

Post scenario validations:
    N/a
"""
