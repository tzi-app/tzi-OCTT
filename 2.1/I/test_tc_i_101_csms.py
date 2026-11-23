"""
Test case name      Set Default Tariff - startTimeOfDay, endTimeOfDay
Test case Id        TC_I_101_CSMS
Use case Id(s)      I07, I12
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS is able to set a tariff with conditions.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - The CSMS supports conditions in Tariffs
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy with condition on startTimeOfDay and endTimeOfDay

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status Accepted

Tool validations
* Step 1:
    Message SetDefaultTariffRequest
    - evseId 0
    - tariff.validFrom must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be <not omitted>
    - tariff.energy.prices[0].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[0].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a
"""
