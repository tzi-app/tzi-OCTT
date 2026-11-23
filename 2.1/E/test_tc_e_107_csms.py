"""
Test case name      Transactions with fixed cost, energy or time - CS specifies time limit
Test case Id        TC_E_107_CSMS
Use case Id(s)      E16
Requirement(s)      …
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where the Charging Station
                    specifies a time limit.

Prerequisite(s)     Test System has TxCtlr.SupportedLimits contains maxTime.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxTime 120
2. The CSMS responds with a TransactionEventResponse

Note: The test system waits for the maxTime transactionLimit to be reached.

3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason TimeLimitReached
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message TransactionEventResponse with:
    - transactionLimit is <omitted>

Post scenario validations:
    N/a
"""
