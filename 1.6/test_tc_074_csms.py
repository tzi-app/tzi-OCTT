"""
Test case name      Update Charge Point Certificate by request of Central System
Test case Id        TC_074_CSMS
Document ref        Table 185, page 159/176 (CompliancyTestTool-TestCaseDocument, 2025-11)
Section             3.21.1 Secure connection setup
System under test   Central System

Description         When SUT Charge Point, the tool shall take on the role of both Central System and Certificate Authority
                    Server. Which means it will sign the certificate with its own certificate.

Purpose             To check if the Central System is able to request the Charge Point to renew its ChargePointCertificate.

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
    [Certificate Authority Server signs the certificate.]
    5. The Central System sends a CertificateSigned.req

    [The Charge Point verifies the validity of the signed certificate.]
    6. The Charge Point responds with a CertificateSigned.conf

    7. The Charge Point disconnects its current connection and reconnects to the Central System
       with the new certificate.
    8. The Central System accepts the incoming connection request using the new certificate.

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
        The certificateChain:
        * The certificateChain field contains valid PEM encoding.
        * The Public key of the client certificate matches the public key generated for the CSR at step 3.
        * The client certificate is signed using the configured security algorithm type.
        * The subject field commonName equals the configured serialNumber.
        * The public key of the client certificate adheres to the minimal OCPP key length
          requirements (RSA: 2048 / ECDSA: 224).

    * Step 6:
        (Message: CertificateSigned.conf)
        The status is Accepted

    * Step 7:
        The Charge Point reconnects to the Central System with the new certificate.

Expected result(s) / behaviour:
    The Charge Point and the Central System are connected.
"""
