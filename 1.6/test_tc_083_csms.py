"""
Test case name      Upgrade Charge Point Security Profile - Accepted
Test case Id        TC_083_CSMS
Section             3.21 Security / 3.21.1 Secure connection setup
Document ref        Table 194, pages 167-169 (CompliancyTestTool-TestCaseDocument 2025-11)
System under test   Central System

Description         The Central System can upgrade the connection using a higher Security Profile, the Central System can
                    send a new value for the SecurityProfile Configuration key.

Purpose             To verify if the Central System is able to upgrade the Charge Point to a higher security profile than currently
                    configured.

Prerequisite(s)     - Next to security profile 2, also security profile 1 and/or 3 must be supported.
                    - Security profile must be set to 1 or 2.

Before (Preparations)
    Configuration State: N/a
    Memory State:
        - CertificateInstalled if SecurityProfile is 1.
        - RenewChargePointCertificate if SecurityProfile is 2.
    Reusable State(s): N/a

Test Scenario
    Manual Action: Send a ChangeConfiguration request for SecurityProfile on the Central System.

    1. The Central System sends a ChangeConfiguration.req
    2. The Charge Point responds with a ChangeConfiguration.conf

    Manual Action: Send a Reset request of type Hard on the Central System.

    3. The Central System sends a Reset.req
    4. The Charge Point responds with a Reset.conf

    5. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile + 1>
    6. The Central System accepts the connection attempt.

    7. The Charge Point sends a BootNotification.req
    8. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0]
    9. The Charge Point sends a StatusNotification.req
    10. The Central System responds with a StatusNotification.conf

    11. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile>
    12. The Central System shall not accept the connection attempt.

    13. The Charge Point reconnects to the Central System with security profile is <Configured securityProfile + 1>
    14. The Central System accepts the connection attempt.

    Note(s):
    - Steps 13-14 are done to restore the connection before ending the testcase.

Tool Validations
    * Step 1:
        (Message: ChangeConfiguration.req)
        - key is SecurityProfile
        - value is <One level higher than the configured security profile>

    * Step 2:
        (Message: ChangeConfiguration.conf)
        - status should be Accepted

    * Step 3:
        (Message: Reset.req)
        - type is Hard

    * Step 4:
        (Message: Reset.conf)
        - status should be Accepted

    * Step 8:
        (Message: BootNotification.conf)
        - status is Accepted

    * Step 9:
        (Message: StatusNotification.req)
        - status should be Available

    * Step 12:
        When upgrading a Charge Point to a higher security profile, a Central System has several options
        regarding which endpoint to use. This affects the way the Central System is able to detect it needs
        to reject the incoming connection attempt.

        In case of having upgraded from security profile 2 to 3, but there is an incoming connection attempt
        using security profile 2:
        - When the same endpoint is used, then it depends on the Central System endpoint configuration.
          - When the Central System does a full switch and only allows TLS handshakes when a client certificate
            is provided, then the TLS handshake is rejected.
          - When the Central System only requires this Charge Point to use a client certificate, then it accepts
            the TLS handshake (because it will be unable to detect which Charge Point is connecting) and it
            rejects the HTTP request to establish the WebSocket connection.
        - When a different port or a whole different endpoint is used for the upgrade, then on the original
          endpoint the Central System accepts the TLS handshake and it rejects the HTTP request to establish
          the WebSocket connection (because this Charge Point is not allowed to connect with security profile 2
          anymore).

        In case of security profile 1, the case is always the same. The Central System shall always reject the
        HTTP request to establish the WebSocket connection, because TLS is required for this Charge Point.

Expected result(s) / behaviour:
    The Charge Point and the Central System are connected.
"""
