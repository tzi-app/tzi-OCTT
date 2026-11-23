"""
Test case name      Settlement at end of transaction - settled by CSMS, receipt by CSMS
Test case Id        TC_C_117_CSMS
Use case Id(s)      C21
Requirement(s)      C21.FR.03, C21.FR.05

Requirement Details:
    C21.FR.03: CSMS SHALL respond with NotifySettlementResponse with receiptUrl.
        Precondition: C21.FR.02 AND PaymentCtrlr.ReceiptByCSMS = true
    C21.FR.05: CSMS SHALL settle the total cost of the transaction with the payment service provider.
        Precondition: When a locally started transaction ends that was authorized by an idToken of type =
                      DirectPayment AND PaymentCtrlr.SettlementByCSMS is true
        Note: The PSP reference to settle the payment session is in idToken.
System under test   CSMS

Description         Settle the amount of charging session via CSMS.

Purpose             To verify if the CSMS is able to settle a transaction directly via PSP.

Prerequisite(s)     - CSMS has an interface to the PSP. - CSMS supports Charging Stations with integrated
                      payment terminals.
                    - Test System has PaymentCtrlr.Enabled = true
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizeAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = true
                    - Value of PaymentCtrlr.ReceiptByCSMS is irrelevant.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - idToken <PspRef>
    - idToken.type DirectPayment
    - transactionInfo.transactionId <transactionId>
    - idToken.additionalInfo[0].additionalIdToken = <not omitted>
    - idToken.additionalInfo[0].type = CardLast4Digits
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - idToken <PspRef>
    - idToken.type DirectPayment
    - triggerReason StopAuthorized
    - transactionInfo.stoppedReason Local
    - transactionInfo.transactionId <transactionId>
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.fixed.exclTax 15.00
    - costDetails.totalCost.fixed.inclTax 18.15 EUR
    - costDetails.totalCost.fixed.taxRate.type MyTax
    - costDetails.totalCost.fixed.taxRate.tax 21
    - costDetails.totalUsage.energy 123
    - costDetails.totalUsage.chargingTime 5
    - costDetails.totalUsage.idleTime 0
    - costDetails.chargingPeriods <omitted>
4. The CSMS responds with a TransactionEventResponse

Note(s):
- The CSMS settles the total cost of the transaction with the payment service provider for amount of 18.15
  EUR.

Tool validations
N/a

Post scenario validations:
    N/a
"""
