"""
Test case name      Set Default Tariff - TariffConditionsSupported is false
Test case Id        TC_I_105_CSMS
Use case Id(s)      I07
Requirement(s)      …
System under test   CSMS

Description         To set the default tariff on the charging station, for example for ad hoc charging, or
                    when there is no driver-specific tariff.

Purpose             To verify if the CSMS is able to process a response indicating ConditionNotSupported.

Prerequisite(s)     - The CSMS supports local cost calculation by CS
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: _Request the CSMS to set a default tariff on EVSE 0 with
- validFrom
- Price for energy in peak hours
- Price for energy other hours

1. The CSMS sends a SetDefaultTariffRequest
2. The Test System responds with SetDefaultTariffResponse with status ConditionsNotSupported

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
    - tariff.energy.prices[1].priceKwh must be <not omitted>
    - tariff.energy.prices[1].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[1].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a
"""
