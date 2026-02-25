"""
Test case name      TLS - Client-side certificate - valid certificate
Test case Id        TC_087_CSMS
Section             3.21 Security
System under test   Central System
Document ref        CompliancyTestTool-TestCaseDocument, Table 197, pages 171-172

Description         The Charge Point uses a client-side certificate to identify itself to the Central System, when using security
                    profile 3.

Purpose             To verify whether the Central System is able to receive a client certificate provided by a Charge Point and
                    setup a secured WebSocket connection.

Prerequisite(s)     The Central System supports security profile 3.

Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): The OCTT closes the connection.

Test Scenario
    1. The Charge Point initiates a TLS handshake and sends a Client Hello to the Central System.
    2. The Central System responds with a Server Hello with the <Configured server certificate>

    3. The Charge Point performs the following actions:
        Send client certificate
        Client Key Exchange
        Certificate verify
        Change Cipher Spec
        Finished

    4. The Central System performs the following actions:
        Change Cipher Spec
        Finished

    5. The Charge Point sends a HTTP upgrade request to the Central System
    6. The Central System upgrades the connection to a (secured) WebSocket connection.

    7. The Charge Point sends a BootNotification.req
    8. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0.]
    9. The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

Tool Validations
    * Step 3:
        The OCTT validates the following before finishing the TLS handshake:
        - The Central System must use TLS version 1.2 or above
        At least the following set of cipher suites must be supported:
            TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
            AND TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
            AND TLS_RSA_WITH_AES_128_GCM_SHA256
            AND TLS_RSA_WITH_AES_256_GCM_SHA384

    Post scenario validations: N/a

Expected result(s) / behaviour: n/a
"""
