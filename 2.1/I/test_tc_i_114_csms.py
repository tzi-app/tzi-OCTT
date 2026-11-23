"""
Test case name      Local Cost Calculation - Change transaction tariff - TariffConditionsSupported is false
Test case Id        TC_I_114_CSMS
Use case Id(s)      I11
Requirement(s)      …
System under test   CSMS

Description         CSMS changes the tariff that is associated with a transaction. This may be needed when
                    dealing with unexpected price changes.

Purpose             To verify if the CSMS is able to process a response indicating ConditionNotSupported.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0
                    - CS has TariffCtrlr.ConditionsSupported[Tariff] = true

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted

Manual Action: Request the CSMS to change the tariff of the transaction with
- validFrom
- Price for energy with condition on startTimeOfDay and endTimeOfDay

2. The CSMS sends a ChangeTransactionTariffRequest with
3. The Test System responds with ChangeTransactionTariffResponse with
    - status ConditionNotSupported

Tool validations
* Step 2:
    Message ChangeTransactionTariffRequest
    - transactionId must be <transaction id>
    - tariff.validFrom must be <not omitted>
    - tariff.energy.prices[0].priceKwh must be <not omitted>
    - tariff.energy.prices[0].conditions.startTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute
    - tariff.energy.prices[0].conditions.endTimeOfDay must be in format as per RFC 3339: time-hour ":"
      time-minute

Post scenario validations:
    N/a

Remarks
TC_I_114_CSMS: Local Cost Calculation - Change transaction tariff - ConditionNotSupported
"""
