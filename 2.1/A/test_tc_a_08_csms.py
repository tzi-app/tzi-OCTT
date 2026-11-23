"""
Test case name      TLS - Client-side certificate - Invalid certificate
Test case Id        TC_A_08_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.405, A00.FR.407, A00.FR.409, A00.FR.410

Requirement Details:
    A00.FR.405: The CSMS SHALL verify that the certificate belongs to this Charging Station by checking that
                the CN (commonName) RDN in the subject field of the certificate contains the unique serial
                number of the Charging Station (see Certificate Properties).
    A00.FR.407: The CSMS SHALL terminate the connection.
        Precondition: NOT A00.FR.429 AND If the Charging Station does not own a valid certificate, or if the
                      certification path is invalid
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.410: The CSMS SHALL authenticate itself by using the CSMS certificate as server side certificate.
                (Same as A00.FR.307)
System under test   CSMS

Description         The Charging Station uses a client-side certificate to identify itself to the CSMS, when
                    using security profile 3.

Purpose             To verify whether the CSMS is able to terminate the connection when the received client
                    certificate is invalid.

Prerequisite(s)     - The CSMS supports security profile 3
                    - This testcase can be executed multiple times, using different kinds of invalid
                      certificates:
                        Unknown certificate
                        expired certificate
                        certificate with commonName that does not equal the serial number of the Charging
                        Station.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System initiates a TLS handshake and sends a Client Hello to the CSMS.
2. The CSMS responds with a Server Hello
    With a server certificate
3. The Test System performs the following actions:
    Send <Configured invalid client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
4. The CSMS deems the client certificate invalid and terminates the connection.
5. The Test System initiates a TLS handshake and sends a Client Hello to the CSMS.
6. The CSMS responds with a Server Hello
    With a server certificate
7. The Test System performs the following actions:
    Send <Configured client certificate>
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
8. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
9. The Test System sends a HTTP upgrade request to the CSMS
10. The CSMS upgrades the connection to a (secured) WebSocket connection.
11. The Test System sends a BootNotificationRequest
    with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
12. The CSMS responds with a BootNotificationResponse
13. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
14. The CSMS responds accordingly.

Tool validations
* Step 12:
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
