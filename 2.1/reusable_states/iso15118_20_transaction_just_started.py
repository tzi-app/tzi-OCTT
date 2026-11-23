"""
State               ISO15118-20 transaction just started
System under test   CSMS
Description         Starts ISO15118-20 transaction
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      State is EVConnectedPreSession

Main

1. The Test System sends an AuthorizeRequest with
   idToken.type eMAID
   idToken.type <Configured ISO15118 idToken>
   iso15118CertificateHashData <hashData’s from MO certificate chain>
2. The CSMS responds with an AuthorizeResponse
   - allowedEnergyTransfer [<csms_allowedEnergyTransferModes>]
3. The Test System sends a TransactionEventRequest with
   eventType Started
   transactionInfo.transactionId <transactionId>
   idToken.additionalInfo.additionalIdToken <Configured EVCCID>
   idToken.additionalInfo.additionalInfo.type EVCCID
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2: Message: AuthorizeResponse - idTokenInfo.status must be Accepted
* Step 4: Message: TransactionEventResponse - idTokenInfo.status must be Accepted
Post condition      N/a

Remarks
Exposes <allowedEnergyTransferModes>
<transactionId>
Prerequisite(s) Test System reported support for V2XChargingCtrlr.V2XEnabled for configured EVSEs with value
true

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.23. Page 1383 - (2026-04) - Additional validation added for certificateStatus
        The certificateStatus should be included in AuthorizeResponse when certificate or
        iso15118CertificateHashData is included in the AuthorizeRequest.

        | State | ISO15118-20 transaction just started |
        | System under test | CSMS |
        | … | |

        | Tool validations |
        | * Step 2: / Message: AuthorizeResponse / - idTokenInfo.status must be Accepted / - certificateStatus
          must be Accepted / * Step 4: / Message: TransactionEventResponse / - idTokenInfo.status must be
          Accepted |
        | Post scenario validations: / N/a |
"""
