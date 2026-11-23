"""
Test case name      Check Transaction status - Transaction with id ongoing - with message in queue
Test case Id        TC_E_29_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.02, E14.FR.04

Requirement Details:
    E14.FR.02: The Charging Station’s response SHALL have ongoingIndicator = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has not stopped yet
    E14.FR.04: The Charging Station’s response SHALL have messagesInQueue = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND It
                      has transaction-related messages to be delivered about the transaction with that
                      transactionId
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages from a specific transaction by sending a GetTransactionStatusRequest with a
                    transactionId. The Test System will respond that there are message(s) queued belonging to
                    the ongoing transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System closes the WebSocket connection.
2. The Test System waits a number of seconds equal to _<Configured Transaction Duration>, then it will
   reconnect to the CSMS._
3. The CSMS sends a GetTransactionStatusRequest
4. The Test System responds with a GetTransactionStatusResponse
    - With ongoingIndicator is true
    - messagesInQueue is true
5. The Test System sends a TransactionEventRequest
    - With eventType is Updated
    - meterValues is present.
    - offline is true
6. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 3:
    Message: GetTransactionStatusRequest
    - transactionId <Generated transactionId from Before>

Post scenario validations:
    N/a
"""
