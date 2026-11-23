"""
Test case name      Check Transaction status - Without transactionId - with message in queue
Test case Id        TC_E_33_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.06, E14.FR.07

Requirement Details:
    E14.FR.06: The Charging Station’s response SHALL NOT have ongoingIndicator set.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId
    E14.FR.07: The Charging Station’s response SHALL have messagesInQueue = true.
        Precondition: The Charging Station receives a GetTransactionStatusRequest without a transactionId AND
                      It has transaction-related messages to be delivered
System under test   CSMS

Description         The CSMS is able to request the status of a transaction and to find out whether there are
                    queued transaction-related messages, using the GetTransactionStatusRequest message.

Purpose             To verify if the CSMS is able to request the status of queued TransactionEventRequest
                    messages by sending a GetTransactionStatusRequest without a transactionId. The Test System
                    will respond that there are message(s) queued.

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
    - With ongoingIndicator is omitted.
    - messagesInQueue is true
5. The Test System sends a TransactionEventRequest
    - With eventType is Updated
    - meterValues is present.
    - offline is true
6. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 3:
    Message: GetTransactionStatusRequest
    - transactionId must be omitted.

Post scenario validations:
    N/a
"""
