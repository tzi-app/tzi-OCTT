"""
Test case name      Integrated Payment Terminal - Cancelation after start of transaction - stopped by EV
                    driver
Test case Id        TC_C_113_CSMS
Use case Id(s)      C20
Requirement(s)      C20.FR.05

Requirement Details:
    C20.FR.05: Charging Station SHALL send a NotifySettlementRequest with transactiondId of transaction,
               idToken of the ad hoc payment in pspRef, and status = Canceled and settlementTime set to
               current time.
        Precondition: C20.FR.04
        Note: This notifies CSMS that the DirectPayment idToken has not been charged for the transaction.
System under test   CSMS

Description         To inform the CSMS that payment has been canceled and the authorization amount has been
                    released.

Purpose             To verify if the CSMS is able to handle Cancelation of a local payment terminal
                    authorization after a transaction has started when the EV driver stops the session at the
                    Charging Station.

Prerequisite(s)     - CSMS supports Charging Stations with integrated payment terminals.
                    - Test System has PaymentCtrlr.AuthorizeDirectPayment = false
                    - Test System has PaymentCtrlr.AuthorizationAmount = 50.00
                    - Test System has PaymentCtrlr.PaymentDetails = "CardLast4Digits"
                    - Test System has PaymentCtrlr.SettlementByCSMS = false

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: Starts and immediately ends a transaction

1. The Test System sends a TransactionEventRequest with
    - eventType Started
    - triggerReason Authorized
    - idToken <pspRef>
    - idToken.type DirectPayment
    - idToken.additionalInfo[0].additionalIdToken = 1234
    - idToken.additionalInfo[0].type = Last4Digits
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.transactionLimit.maxCost 50.00
2. The CSMS responds with a TransactionEventResponse
3. The Test System sends a TransactionEventRequest with
    - eventType Ended
    - idToken <pspRef>
    - idToken.type DirectPayment
    - idToken.additionalInfo[0].additionalIdToken = 1234
    - idToken.additionalInfo[0].type = Last4Digits
    - transactionInfo.transactionId <transactionId>
    - transactionInfo.stoppedReason Local
    - triggerReason StopAuthorized
    - costDetails.totalCost.currency EUR
    - costDetails.totalCost.typeOfCost NormalCost
    - costDetails.totalCost.total 0
    - costDetails.totalUsage.energy 0
    - costDetails.totalUsage.chargingTime 0
    - costDetails.totalUsage.idleTime 0
4. The CSMS responds with a TransactionEventResponse
5. The Test System sends a NotifySettlementRequest with
    - transactionId <transactionId>
    - pspRef <pspRef>
    - status Canceled
    - settlementTime <Equal to timestamp step 3>
    - settlementAmount 0
    - receiptUrl <omitted>
6. The CSMS responds with a NotifySettlementResponse

Tool validations
N/a

Post scenario validations:
    N/a
"""
