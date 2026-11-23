"""
Test case name      Transactions with fixed cost, energy or time - CS specifies energy limit
Test case Id        TC_E_106_CSMS
Use case Id(s)      E16
Requirement(s)      …
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where the Charging Station
                    specifies an energy limit.

Prerequisite(s)     Test System has TxCtrlr.SupportedLimits contains maxEnergy.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxEnergy 6000
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason EnergyLimitReached
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message TransactionEventResponse with:
    - transactionLimit is <omitted>

Post scenario validations:
    N/a
"""
