"""
Test case name      Transactions with fixed cost, energy or time - CSMS calculates costs and specifies cost
                    limit
Test case Id        TC_E_109_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.02, E16.FR.11

Requirement Details:
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
    E16.FR.11: CSMS SHALL provide cost updates to Charging Station in TransactionEventResponse or
               CostUpdatedRequest.
        Precondition: When a transactionLimit.maxCost is active AND ( TariffCostCtrlr.Enabled[Tariff] = false
                      OR when CSMS has not provided a (default) tariff plan )
        Note: Central cost calculation is used.
System under test   CSMS

Description         CSMS will set a limit the transaction for the specified cost. CS will use central cost
                    calculation.

Purpose             To verify whether the CSMS correctly sends cost when central cost calculation is used.

Prerequisite(s)     - CSMS supports setting cost limits
                    - Test System has TxCtrlr.SupportedLimits containing maxCost
                    - Test System has TariffCostCtrlr.Enabled[Cost] is false

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. The Test System sends a AuthorizeRequest
    - With idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
2. The CSMS responds with a AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - With eventType is Started
    - triggerReason is ChargingStateChanged
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.chargingState is Charging
4. The CSMS responds with a TransactionEventResponse
5 The Test System sends a TransactionEventRequest with
    - triggerReason is LimitSet
    - transactionInfo.transactionLimit.maxCost is 10
6 The CSMS responds with TransactionEventResponse
7. The CSMS sends a CostUpdatedRequest
8. The Test System responds with a CostUpdatedResponse

Note: Sending a CostUpdatedRequest is not required, but if CSMS does send it, the validation applies.

Tool validations
* Step 2:
    Message: AuthorizeResponse
    - idTokenInfo.status must be Accepted
* Step 4:
    Message: TransactionEventResponse
    - totalCost must be <not omitted>
    - transactionInfo.transactionLimit.maxEnergy must be <omitted>
    - transactionInfo.transactionLimit.maxTime must be <omitted>
    - transactionInfo.transactionLimit.maxCost must be 10
* Step 6:
    Message: TransactionEventResponse
    - totalCost must be <not omitted>
    - transactionInfo.transactionLimit must be <omitted>
* Step 8:
    Message: CostUpdatedRequest
    - transactionId must be <transactionId>
    - totalCost must be <not omitted>

Post scenario validations:
    N/a
"""
