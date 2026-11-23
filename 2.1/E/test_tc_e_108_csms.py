"""
Test case name      Transactions with fixed cost, energy or time - CS calculates costs and specifies limit
Test case Id        TC_E_108_CSMS
Use case Id(s)      E16
Requirement(s)      …
System under test   CSMS

Description         EV Driver or CSMS specifies a limit in cost, energy, state of charge or time for
                    transaction.

Purpose             To verify whether the CSMS correctly handles transactions where the Charging Station uses
                    local cost calculation and specifies a cost limit.

Prerequisite(s)     - Test System has TariffCostCtrlr.Enabled[Cost] is true
                    - Test System has TariffCostCtrlr.Enabled[RunningCost] is true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: Trigger CSMS to configure a tariff with 1 EUR / minute for charging time

1. The CSMS sends a SetDefaultTariffRequest with
    - evseId 0
    - tariff.tariffId <not omitted>
    - tariff.currency EUR
    - tariff.chargingTime.prices[0].priceMinute 1.00
2. The Test System responds with a SetDefaultTariffResponse
3. Execute Reusable State EnergyTransferStarted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason LimitSet
    - transactionInfo.transactionLimit.maxCost 2.00
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 1.00
    - costDetails.totalCost.total.inclTax 1.00
    - costDetails.totalUsage.chargingTime 60
    - costDetails.totalUsage.idleTime <not omitted>
5. The CSMS responds with a TransactionEventResponse
6. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason RunningCost
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 1.50
    - costDetails.totalCost.total.inclTax 1.50
    - costDetails.totalUsage.chargingTime 90
    - costDetails.totalUsage.idleTime <not omitted>
7. The CSMS responds with a TransactionEventResponse
8. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason CostLimitReached
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.chargingTime.inclTax 2.00
    - costDetails.totalCost.total.inclTax 2.00
    - costDetails.totalUsage.chargingTime 120
    - costDetails.totalUsage.idleTime <not omitted>
9. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: SetDefaultTariffRequest
    - evseId must be <evse id>
    - tariff.tariffId must be <not omitted>
    - tariff.currency must be EUR
    - tariff.chargingTime.prices[0].priceMinute must be 1.00
* Step 5:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>
* Step 7:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>
* Step 9:
    Message: TransactionEventResponse
    - totalCost must be <omitted>
    - transactionLimit must be <omitted>

Post scenario validations:
    N/a
"""
