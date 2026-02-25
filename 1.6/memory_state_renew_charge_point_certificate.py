"""
Memory State        RenewChargePointCertificate
State Id            MS_RENEW_CHARGE_POINT_CERTIFICATE
OCPP version        1.6J (Security Extension)
System under test   Central System (CS)
Document ref        CompliancyTestTool-TestCaseDocument, Table 204, pages 175-176

Description         This state will renew the client certificate on the Charge Point.

Purpose             To bring the system into a known state where the Charge Point's client certificate
                    has been renewed through the full CSR flow (trigger -> CSR -> sign -> install).

Before (Preparations):
    Configuration State(s):
        - CpoName = <Configured Vendor Name> (Optional)
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario
                    Charge Point (Tool)                     Central System (SUT)

1.                                                          The Central System sends an
                                                            ExtendedTriggerMessage.req with:
                                                            - requestedMessage = SignChargePointCertificate
                                                            - connectorId = <Omitted>
2. The Charge Point responds with an
   ExtendedTriggerMessage.conf.
   [The Charge Point generates a new public/private
    key pair and generates a Certificate Signing Request.]
3. The Charge Point sends a SignCertificate.req.
                                                            (TODO: doc does not list fields for SignCertificate.req;
                                                             expected field from OCPP spec: csr = <PEM-encoded CSR>)
                                                         4. The Central System responds with a
                                                            SignCertificate.conf with:
                                                            - status = Accepted
                                                            [Certificate Authority Server signs the certificate.]
                                                         5. The Central System sends a CertificateSigned.req.
                                                            (TODO: doc does not list fields for CertificateSigned.req;
                                                             expected field from OCPP spec:
                                                             certificateChain = <PEM-encoded signed certificate chain>)
6. The Charge Point responds with a
   CertificateSigned.conf.
   [The Charge Point verifies the validity of the signed
    certificate.]

Tool validations:
    * Step 2:
        (Message: ExtendedTriggerMessage.conf)
        - status should be Accepted
    * Step 6:
        (Message: CertificateSigned.conf)
        - status should be Accepted

Expected result(s) / behaviour:
    State is RenewChargePointCertificate.
"""
