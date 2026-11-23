"""
Test case name      Settlement at end of transaction - settled by CS, receipt by CSMS
Test case Id        TC_C_118_CSMS
Use case Id(s)      C21
Requirement(s)      C21.FR.03

Requirement Details:
    C21.FR.03: CSMS SHALL respond with NotifySettlementResponse with receiptUrl.
        Precondition: C21.FR.02 AND PaymentCtrlr.ReceiptByCSMS = true
System under test   CSMS

Description         In order to test that Charging Station supports settlement at the end of a transaction
                    where the settlement is handled by the Charging Station and the receipt is provided by the
                    CSMS.

Purpose             To verify that the CSMS can properly handle a transaction where the settlement is done by
                    the Charging Station and the CSMS provides the receipt.

Prerequisite(s)     - CSMS supports settlement at the end of a transaction. - CSMS supports Charging Stations
                      with integrated payment terminals.
                    - Test System has PaymentCtrlr.Enabled = true
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizationAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = false
                    - Test System has PaymentCtrlr.ReceiptByCSMS = true
                    - CSMS lets the CS handle the settlement at the end of a transaction, but the CSMS
                      provides receipts.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken <configured PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - idToken.additionalInfo[0].additionalIdToken = <not omitted>
    - idToken.additionalInfo[0].type = CardLast4Digits
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - triggerReason StopAuthorized
    - idToken <configured PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.stoppedReason Local
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods[ <omitted>
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a NotifySettlementRequest with
    - transactionId <transactionId>
    - pspRef <configured PspRef>
    - status Settled
    - settlementTime <not omitted>
    - settlementAmount 18.15
    - receiptUrl <omitted>
6. The CSMS responds with a NotifySettlementResponse

Tool validations
* Step 6:
    Message NotifySettlementResponse
    - receiptUrl must be <not omitted>

Post scenario validations:
    - Verify that the receipt URL provided by the CSMS is valid and accessible.
"""
