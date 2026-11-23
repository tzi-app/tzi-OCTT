"""
ADDED by OCPP 2.1 Edition 2 errata 2026-09 (5.3, 6.1.1) - transcribed from the errata document.

Test case name      Update Charging Station Certificate by request of CSMS - Success - V2G Certificate -20
Test case Id        TC_A_112_CSMS
Use case Id(s)      A02 & F06
Requirement(s)      A02.FR.11, F06.FR.01

Requirement Details:
    A02.FR.11: The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station
                    certificate using the TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update its V2G
                    Certificate.

Prerequisite(s)     The CSMS supports ISO 15118-20.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a TriggerMessageRequest
2. The Test System responds with a TriggerMessageResponse
    - status Accepted
3. The Test System sends a SignCertificateRequest
    - csr Generated CSR based on:
        - <Configured Country>
        - <Configured Organization>
        - <Configured OrganizationalUnit>
    - certificateType V2G20Certificate
    - requestId <Generated requestId>
4. The CSMS responds with a SignCertificateResponse
5. The CSMS sends a CertificateSignedRequest
6. The Test System responds with a CertificateSignedResponse
    - status Accepted

Tool validations
* Step 1:
    Message: TriggerMessageRequest
    - requestedMessage SignV2G20Certificate
* Step 4:
    Message: SignCertificateResponse
    - status Accepted
* Step 5:
    Message: CertificateSignedRequest
    - certificateType V2G20Certificate
    - certificateChain <Certificate generated from the received CSR from step 3 and signed by the V2G Root or
      SubCA certificate from the configured V2G certificate chain>

    NOTE: The Test System will validate the certificate, but if the following validation fail, the testcase
          will NOT FAIL, because generating the certificate is probably not be done by the CSMS.

    - The key must be at least 224 bits long.
    - The received certificate must be transmitted in the X.509 format encoded in Privacy-Enhanced Mail (PEM)
      format.

Post scenario validations:
    N/a
"""
