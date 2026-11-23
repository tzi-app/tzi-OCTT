"""
Test case name      Set Default Tariff - validations
Test case Id        TC_I_106_CSMS
Use case Id(s)      I07, I09
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS supports configuring setting local cost calculation.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate
- Price for reservationTime with a taxRate

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to set a default tariff on EVSE 1 with
- validFrom
- Price for energy with a taxRate
- Price for chargingTime with a taxRate
- Price for idleTime with a taxRate
- Price for fixedFee with a taxRate
- Price for minCost with a taxRate
- Price for maxCost with a taxRate
- Price for reservationFixed with a taxRate

3. The CSMS sends a SetDefaultTariffRequest with
4. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to get the tariffs for EVSE 0

5. The CSMS sends a GetTariffsRequest
6. The Test System responds with GetTariffsResponse with
    - status Accepted
    - tariffAssignments[0].tariffId <value of tariffId from step 1>
    - tariffAssignments[0].tariffKind DefaultTariff
    - tariffAssignments[0].evseIds [ 2 ]
    - tariffAssignments[0].validFrom must be <not omitted>
    - tariffAssignments[1].tariffId <value of tariffId from step 3>
    - tariffAssignments[1].tariffKind DefaultTariff
    - tariffAssignments[1].evseIds [ 1 ]
    - tariffAssignments[1].validFrom must be <not omitted>

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.tariffId must be <not omitted>
    - tariff.validFrom must be _<not omitted>
    - tariff.energy must be <not omitted>
    - tariff.energy.taxRates must be <not omitted>
    - tariff.chargingTime must be <not omitted>
    - tariff.chargingTime.taxRates must be <not omitted>
    - tariff.idleTime must be <not omitted>
    - tariff.idleTime.taxRates must be <not omitted>
    - tariff.fixedFee must be <not omitted>
    - tariff.fixedFee.taxRates must be <not omitted>
    - tariff.minCost must be <not omitted>
    - tariff.minCost.exclTax or tariff.minCost.inclTax must be <not omitted> (at least one must exist)
    - tariff.minCost.taxRates must be <not omitted>
    - tariff.maxCost must be <not omitted>
    - tariff.maxCost.exclTax or tariff.maxCost.inclTax must be <not omitted> (at least one must exist)
    - tariff.maxCost.taxRates must be <not omitted>
    - tariff.reservationTime must be <not omitted>
    - tariff.reservationTime.taxRates must be <not omitted>
* Step 3:
    Message SetDefaultTariffRequest
    - evseId 1
    - tariff.tariffId must be <Different from tariffId step 1>
    - tariff.validFrom must be _<not omitted>
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
    - tariff.reservationFixed must be <not omitted>
    - tariff.reservationFixed.taxRates must be <not omitted>
* Step 5:
    Message GetTariffsRequest
    - evseId must be 0

Post scenario validations:
    N/a
"""
