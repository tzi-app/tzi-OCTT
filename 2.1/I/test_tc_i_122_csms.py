"""
Test case name      Local Cost Calculation - Cost Details of Transaction
Test case Id        TC_I_122_CSMS
Use case Id(s)      I12
Requirement(s)      …
System under test   CSMS

Description         Charging Station calculates cost of the transaction locally and returns a break-down of
                    the cost at end of the transaction for every charging period for which a different tariff
                    element was active. CSMS can use this to generate invoices or Charge Detail Records for
                    EMSPs.

Purpose             To verify if the CSMS is able to process the cost details sent by the Charging Station.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.Enabled[Cost] = true
                    - CS has TariffCtrlr.Enabled[RunningCost] = true
                    - CS has TariffCtrlr.Interval[Cost] = 30
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: _Request the CSMS to set a default tariff on EVSE 0 with
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted
3. Execute Reusable State EnergyTransferStarted
4. The Test System sends a TransactionEventRequest with
    - eventType Updated
    - triggerReason RunningCost
    - costDetails.failureToCalculate <omitted>
    - costDetails.failureReason <omitted>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.reservation <omitted>
    - costDetails.totalCost.fixed.exclTax 15
    - costDetails.totalCost.fixed.inclTax 15.75
    - costDetails.totalCost.fixed.taxRates[0].type t5_0
    - costDetails.totalCost.fixed.taxRates[0].tax 5.0
    - costDetails.chargingPeriods[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of step 1>
    - costDetails.chargingPeriods[0].startPeriod <txStartDateTime>
    - costDetails.chargingPeriods[0].dimensions[0].type ChargingTime
    - costDetails.chargingPeriods[0].dimensions[0].volume 15
    - costDetails.chargingPeriods[0].dimensions[1].type Energy
    - costDetails.chargingPeriods[0].dimensions[1].volume 12
5. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.energy must be <not omitted>
    - tariff.energy.taxRates must be <not omitted>
    - tariff.chargingTime must be <not omitted>
    - tariff.chargingTime.taxRates must be <not omitted>
    - tariff.idleTime must be <not omitted>
    - tariff.idleTime.taxRates must be <not omitted>
    - tariff.fixedFee must be <not omitted>
    - tariff.fixedFee.taxRates must be <not omitted>
    - tariff.minCost must be <not omitted>
    - tariff.minCost.exclTax must be <not omitted>
    - tariff.minCost.inclTax must be <not omitted>
    - tariff.minCost.taxRates must be <not omitted>
    - tariff.maxCost must be <not omitted>
    - tariff.maxCost.exclTax must be <not omitted>
    - tariff.maxCost.inclTax must be <not omitted>
    - tariff.maxCost.taxRates must be <not omitted>

Post scenario validations:
    N/a
"""
