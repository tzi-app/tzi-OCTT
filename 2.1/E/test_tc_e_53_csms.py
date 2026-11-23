"""
Test case name      Reset Sequence Number - CSMS accepting seqNo = 0 at start of transaction
Test case Id        TC_E_53_CSMS
Use case Id(s)      E01
Requirement(s)      E01.FR.07

Requirement Details:
    E01.FR.07: The Charging Station SHALL set the message’s seqNo field as specified in Sequence Number
               Generation.
        Precondition: When a TransactionEventRequest has to be created
System under test   CSMS

Description         OCPP 2.0.1 Edition 2 recommends that seqNo starts at 0 for every transaction. CSMS must
                    therefore be robust to a seqNo that is not continuously increasing, but that restarts for
                    new transactions. Since a TransactionEventRequest cannot be rejected, this can only be
                    detected by either the complete absence of a TranactionEventResponse from CSMS or an
                    otherwise misbehaving CSMS.

Purpose             To verify if the CSMS accepts that a new transactions starts with a seqNo = 0.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted
    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
2. Execute Reusable State EVDisconnected
3. Execute Reusable State EnergyTransferStarted
    Note(s): New transaction will use seqNo 0 for the first TransactionEventRequest.
4. Execute Reusable State EVDisconnected

Tool validations
* Step 1:
    CSMS accepts the message TransactionEventRequest with eventType = Started and seqNo = 0 and answers with a
    TransactionEventResponse message.
* Step 3:
    CSMS accepts the message TransactionEventRequest with eventType = Started and seqNo = 0 and answers with a
    TransactionEventResponse message.

Post scenario validations:
    N/a
"""
