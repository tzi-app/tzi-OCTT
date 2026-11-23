"""
State               RenewChargingStationCertificate
System under test   CSMS
Description         The ChargingStationCertificate is renewed using A02/A03
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

Manual Action: Request the CSMS to send a Trigger Message Request with requestedMessage
               SignChargingStationCertificate

1. The CSMS sends a TriggerMessageRequest With requestedMessage SignChargingStationCertificate
2. The Test System sends a TriggerMessageResponse with status Accepted
3 The Test System sends a SignCertificateRequest
4. The CSMS responds with a SignCertificateResponse with status Accepted
5. The CSMS sends a CertificateSignedRequest With certificateChain <Certificate generated from the received
   CSR from step 3 and signed by the configured CSMS Root certificate>
   certificateType ChargingStationCertificate
6. The Test System sends a CertificateSignedResponse with status Accepted

Tool validations
* Step 1: Message: TriggerMessageRequest - requestedMessage must be SignChargingStationCertificate
* Step 4: Message: SignCertificateResponse - status must be Accepted
* Step 5: Message: CertificateSignedRequest
  - certificateChain <Certificate generated from the received CSR from step 3 and signed by the configured
    CSMS Root certificate>
  - certificateType must be ChargingStationCertificate
Post condition      N/a
"""
