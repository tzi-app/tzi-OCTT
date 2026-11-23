"""
Test case name      TLS - Client-side certificate - valid certificate
Test case Id        TC_A_07_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.409, A00.FR.410, A00.FR.415, A00.FR.416, A00.FR.421

Requirement Details:
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.410: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate.
                (Same as A00.FR.307)
    A00.FR.415: The communication channel SHALL be secured using Transport Layer Security (TLS) [4]. (Same as
                A00.FR.312)
    A00.FR.416: The Charging Station and CSMS SHALL only use TLS v1.2 or above. (Same as A00.FR.313)
    A00.FR.421: The CSMS SHALL support at least the following four cipher suites:
                TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256 TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
                TLS_RSA_WITH_AES_128_GCM_SHA256 TLS_RSA_WITH_AES_256_GCM_SHA384 (Same as A00.FR.318) Note: The
                CSMS will have to provide 2 different certificates to support both cipher suites. Also when
                using security profile 3, the CSMS should be capable of generating client side certificates
                for both cipher suites.
System under test   CSMS

Description         The Charging Station uses a client-side certificate to identify itself to the CSMS, when
                    using security profile 3.

Purpose             To verify whether the CSMS is able to receive a client certificate provided by a Charging
                    Station and setup a secured WebSocket connection.

Prerequisite(s)     The CSMS supports security profile 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System terminates the connection and initiates a TLS handshake and sends a Client Hello to the
   CSMS.
2. The CSMS responds with a Server Hello
    With the <Configured server certificate>
3. The Test System performs the following actions:
    Send <Configured client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
4. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
5. The Test System sends a HTTP upgrade request to the CSMS
6. The CSMS upgrades the connection to a (secured) WebSocket connection.
7. The Test System sends a BootNotificationRequest
    with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
8. The CSMS responds with a BootNotificationResponse
9. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
10. The CSMS responds accordingly.

Tool validations
* Step 3:
    The Test System validates the following before finishing the TLS handshake:
    - The CSMS must use TLS version 1.2 or above
    At least the following set of cipher suites must be supported:
    TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    AND
    TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    AND
    TLS_RSA_WITH_AES_128_GCM_SHA256
    AND
    TLS_RSA_WITH_AES_256_GCM_SHA384
* Step 8:
    Message: BootNotificationResponse
    with status Accepted

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.3. Page 24 - (2026-02) - A00.FR.308 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        |  | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. |  |
        | New | A00.FR.308 |  | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] |  |

    2.4. Page 26 - (2026-02) - A00.FR.403 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] | |
        | New | A00.FR.403 | | The CSMS SHALL verify the certification path of the Charging Station’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26] | |

    2.6. Page 27 - (2026-02) - A00.FR.411 - Additional requirement references
        (Part 2 errata - applies to this test via use case A00)
        | | ID | Precondition | Requirement definition | Note |
        | Old | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3]. (Same as
          A00.FR.308) | |
        | New | A00.FR.411 | | The Charging Station SHALL verify the certification path of the CSMS’s
          certificate according to the path validation rules established in Section 6 of [3] and Section 4 of
          [26]. (Same as A00.FR.308) | |
"""
