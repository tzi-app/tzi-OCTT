"""
Test case name      Update Charging Station Certificate by request of CSMS - Success - Charging Station
                    Certificate
Test case Id        TC_A_11_CSMS
Use case Id(s)      A02 & F06
Requirement(s)      A02.FR.11, A02.FR.14, F06.FR.01

Requirement Details:
    A02.FR.11: The CSMS SHALL set status to Accepted in the SignCertificateResponse.
        Precondition: Upon receipt of a SignCertificateRequest AND It is able to process the request
    A02.FR.14: It is RECOMMENDED for the CSMS to set the certificateType field in the CertificateSignedRequest
               to the type of certificate in the SignCertificateRequest.
        Precondition: When receiving a SignCertificateRequest with certificateType included
    F06.FR.01: In the TriggerMessageRequest message, the CSMS SHALL indicate which message(s) it wishes to
               receive.
System under test   CSMS

Description         The CSMS is able to request the Charging Station to update its charging station
                    certificate using the TriggerMessageRequest message.

Purpose             To verify if the CSMS is able to request the Charging Station to update its Charging
                    Station Certificate.

Prerequisite(s)     The CSMS supports security profile 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State RenewChargingStationCertificate
2. The Test System disconnects its current connection and reconnects to the CSMS with the new certificate.
3. The CSMS accepts the incoming connection request using the new certificate.

Tool validations
N/a

Post scenario validations:
    The Test System and the CSMS are connected.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.7. Page 37 - (2026-02) - A02.FR.02 - Requirement reference correction
        (Part 2 errata - applies to this test via use case A02)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 4.2.1.3 of [16]. | |
        | New | A02.FR.02 | | The Charging Station SHALL generate a new public / private key pair using one of
          the key generation functions described in Section 8.1 of [27] . | |
"""
