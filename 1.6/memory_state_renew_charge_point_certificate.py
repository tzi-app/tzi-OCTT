"""
Memory State        RenewChargePointCertificate
State Id            MS_RENEW_CHARGE_POINT_CERTIFICATE
OCPP version        1.6J (Security Extension)
System under test   Charge Point (CP)
Document ref        CompliancyTestTool-TestCaseDocument-CSMS-Section3, Table 120, page 107/176

Description         This state will ensure that a client certificate is installed on the Charge Point.

Before (Preparations):
    Configuration State(s):
        - CpoName is <Configured Vendor Name>
    Memory State(s): n/a
    Reusable State(s): n/a

Scenario
                    Charge Point (SUT)                      Central System (Tool)

                                                         1. The Central System sends an
                                                            ExtendedTriggerMessage.req with:
                                                            - requestedMessage = SignChargePointCertificate
                                                            - connectorId = <Omitted>
2. The Charge Point responds with a
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
