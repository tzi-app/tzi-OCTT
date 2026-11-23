"""
Test case name      Clear Tariffs - DefaultTariff
Test case Id        TC_I_110_CSMS
Use case Id(s)      I10
Requirement(s)      …
System under test   Charging Station

Description         To clear previously set tariffs on the charging station.

Purpose             To verify if the CSMS is able to clear tariffs.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0.

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Manual Action: Request the CSMS to clear only the tariff set in step 1.

3. The CSMS sends a ClearTariffsRequest
4. The Test System responds with ClearTariffsResponse with
    - clearTariffsResult[0].tariffId <SetDefaultTariffRequest.tariff.tariffId of step 1>
    - clearTariffsResult[0].status Accepted

Manual Action: Request the CSMS to clear all tariffs.

5. The CSMS sends a ClearTariffsRequest
6. The Test System responds with ClearTariffsResponse with
    - clearTariffsResult[0].tariffId <omitted>
    - clearTariffsResult[0].status NoTariff

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.tariffId must be <not omitted>
* Step 3:
    Message ClearTariffsRequest
    - tariffIds[0] must be _<SetDefaultTariffRequest.tariff.tariffId of step 1>
* Step 5:
    Message ClearTariffsRequest
    - tariffIds must be <omitted>

Post scenario validations:
    N/a
"""
