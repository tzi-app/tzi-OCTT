"""
Test case name      Local Cost Calculation - Change transaction tariff - TariffMaxElements
Test case Id        TC_I_113_CSMS
Use case Id(s)      I11
Requirement(s)      …
System under test   CSMS

Description         CSMS changes the tariff that is associated with a transaction. This may be needed when
                    dealing with unexpected price changes.

Purpose             To verify if the CSMS is able to process a response indicating TooManyElements.

Prerequisite(s)     - The CSMS supports local cost calculation by CS.
                    - CS has TariffCtrlr.Enabled[Tariff] = true
                    - CS has TariffCtrlr.MaxElements[Tariff] > 0

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Execute Reusable State EnergyTransferStarted

Manual Action: Request the CSMS to change the tariff of the transaction

2. The CSMS sends a ChangeTransactionTariffRequest with
3. The Test System responds with ChangeTransactionTariffResponse with
    status TooManyElements

Tool validations
* Step 2:
    Message ChangeTransactionTariffRequest
    - transactionId must be <transaction id>

Post scenario validations:
    N/a
"""
