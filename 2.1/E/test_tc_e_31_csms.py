"""
Test case name      Check Transaction status - Transaction with id ended - with message in queue
Test case Id        TC_E_31_CSMS
Use case Id(s)      E14
Requirement(s)      E14.FR.03, E14.FR.04

Requirement Details:
    E14.FR.03: The Charging Station’s response SHALL have ongoingIndicator = false.
        Precondition: The Charging Station receives a GetTransactionStatusRequest with a transactionId AND The
                      transaction with that transactionId has stopped
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
                    an ended transaction with the requested id.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System closes the WebSocket connection.
2. The Test System waits a number of seconds equal to _<Configured Transaction duration>, then it will
   reconnect to the CSMS._
3. The Test System sends a StatusNotificationRequest
    - With evseId is <Configured evseId>
    - connectorId is <Configured connectorId>
    - connectorStatus is Available
4. The CSMS responds with a StatusNotificationResponse
5. The Test System sends a TransactionEventRequest
    - With eventType is Ended
    - offline is true
    - triggerReason is EVCommunicationLost
    - transactionInfo.chargingState is Idle
    - seqNo <Skips two sequence number values>
6. The CSMS responds with a TransactionEventResponse
7. The CSMS sends a GetTransactionStatusRequest
8. The Test System responds with a GetTransactionStatusResponse
    - With ongoingIndicator is false
    - messagesInQueue is true
9. The Test System sends a TransactionEventRequest
    - With triggerReason is StopAuthorized
    - eventType is Updated
    - offline is true
    - seqNo <This is the first of the two skipped values>
10. The CSMS responds with a TransactionEventResponse
11. The Test System sends a TransactionEventRequest
    - With triggerReason is ChargingStateChanged
    - transactionInfo.chargingState is EVConnected
    - eventType is Updated
    - offline is true
    - seqNo <This is the second of the two skipped values>
12. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 5:
    Message: GetTransactionStatusRequest
    - transactionId <Generated transactionId from Before>

Post scenario validations:
    N/a

Remarks
Transcriber's note (not printed in the document): the Tool validations are printed under "Step 5" although the
GetTransactionStatusRequest is step 7 of the scenario; this is kept as printed. In the scenario table, step 8
(Charging Station column) and step 7 (CSMS column) share one row; they are listed here in numeric order.
"""
