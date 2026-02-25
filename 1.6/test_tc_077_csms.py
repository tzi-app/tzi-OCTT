"""
Test case name      Invalid ChargePointCertificate Security Event
Test case Id        TC_077_CSMS
Section             3.21.2 Security event/logging
System under test   Central System
Document reference  Table 189, page 162/176 (OCPP Compliancy Testing Tool - TestCaseDocument, 2025-11)

Description         The Charge Point notifies the Central System of an invalid certificate.

Purpose             To check if the Central System can handle when a Charge Point registers a security event and notifies the
                    Central System about it.

Prerequisite(s)     The Central System supports security profile 3.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    1. The Central System sends an ExtendedTriggerMessage.req
    2. The Charge Point responds with an ExtendedTriggerMessage.conf

    [The Charge Point generates a new public/private key pair and generates a Certificate Signing Request.]
    3. The Charge Point sends a SignCertificate.req

    4. The Central System responds with a SignCertificate.conf

    [The Charge Point verifies the validity of the signed certificate.]
    5. The Central System sends a CertificateSigned.req

    6. The Charge Point responds with a CertificateSigned.conf

    7. The Charge Point sends a SecurityEventNotification.req
    8. The Central System responds with a SecurityEventNotification.conf

Tool Validations
    * Step 1:
        (Message: ExtendedTriggerMessage.req)
        The requestedMessage is SignChargePointCertificate
        The connectorId is <Omitted>

    * Step 2:
        (Message: ExtendedTriggerMessage.conf)
        The status is Accepted

    * Step 4:
        (Message: SignCertificate.conf)
        The status is Accepted

    * Step 5:
        (Message: CertificateSigned.req)
        The certificate is <Signed ChargePointCertificate>

    * Step 6:
        (Message: CertificateSigned.conf)
        The status is Rejected

    * Step 7:
        (Message: SecurityEventNotification.req)
        The type is InvalidChargePointCertificate

Expected result(s) / behaviour: n/a
"""
