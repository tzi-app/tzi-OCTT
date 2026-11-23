"""
Test case name      Transactions with fixed cost, energy or time - CSMS and CS both specify limits
Test case Id        TC_E_102_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.01, E16.FR.02, E16.FR.03

Requirement Details:
    E16.FR.01: Charging Station SHALL send a TransactionEventRequest with triggerReason = LimitSet and include
               this limit once in the field transactionInfo.transactionLimit.
        Precondition: When Charging Station sets or changes a limit to the transaction in cost, energy, SoC or
                      time
        Note: This is usually a limit entered by EV Driver. Sending transactionLimit may be part of another
              triggerReason if multiple triggers apply, see E02.FR.17.
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
    E16.FR.03: Charging Station SHALL send a TransactionEventRequest with triggerReason = LimitSet and include
               the supported limit(s) once in the field transactionInfo.transactionLimit.
        Precondition: E16.FR.02 AND at least one of the limits in transactionLimit is supported by the
                      Charging Station
        Note: This confirms to CSMS that the limit is set. For example, a prepaid cost limit. See also
              E16.FR.13.
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where both the CSMS and Charging
                    Station specify limits.

Prerequisite(s)     - CSMS allows specifying an energy limit.
                    - Test System has TxCtrlr.SupportedLimits contains maxEnergy.

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxEnergy 6000
2. The CSMS responds with a TransactionEventResponse

Manual action: Configure the CSMS to override the max energy limit to 10000 (Wh).

3. The Test System sends a TransactionEventRequest with
    - eventType Updated
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transctionLimit.maxEnergy is 10000
6. The CSMS responds with a TransactionEventResponse
7. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason EnergyLimitReached
8. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 4:
    Message: TransactionEventResponse
    - transactionLimit.maxEnergy must be 10000
* Step 6:
    Message: TransactionEventResponse
    - transactionLimit is <omitted>

Post scenario validations:
    N/a
"""
