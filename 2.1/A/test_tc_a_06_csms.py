"""
Test case name      TLS - server-side certificate - TLS version too low
Test case Id        TC_A_06_CSMS
Use case Id(s)      A00
Requirement(s)      A00.FR.314, A00.FR.315, A00.FR.409, A00.FR.416, A00.FR.417, A00.FR.418

Requirement Details:
    A00.FR.314: Both of these endpoints SHALL check the version of TLS used.
    A00.FR.315: The CSMS SHALL terminate the connection.
        Precondition: A00.FR.314 AND The CSMS detects that the Charging Station only allows connections using
                      an older version of TLS, or only allows SSL
    A00.FR.409: The CSMS SHALL act as the TLS server. (Same as A00.FR.306)
    A00.FR.416: The Charging Station and CSMS SHALL only use TLS v1.2 or above. (Same as A00.FR.313)
    A00.FR.417: Both of these endpoints SHALL check the version of TLS used. (Same as A00.FR.314)
    A00.FR.418: The CSMS SHALL terminate the connection. (Same as A00.FR.315)
        Precondition: A00.FR.417 AND The CSMS detects that the Charging Station only allows connections using
                      an older version of TLS, or only allows SSL
System under test   CSMS

Description         The CSMS uses a server-side certificate to identify itself to the Charging Station, when
                    using security profile 2 or 3.

Purpose             To verify whether the CSMS is able to terminate the connection when it notices the used
                    TLS version is lower than 1.2.

Prerequisite(s)     The CSMS supports security profile 2 and/or 3

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System terminates the connection and initiates a TLS handshake with a TLS version lower than 1.2
   and sends a Client Hello to the CSMS.
2. The CSMS notices that the TLS version is lower than 1.2 and terminates the connection.
3. The Test System initiates a TLS handshake with TLS version 1.2 or higher and sends a Client Hello to the
   CSMS.
4. The CSMS responds with a Server Hello
    With the <Configured server certificate>
5. The Test System performs the following actions:
    Send client certificate
    Client Key Exchange
    Certificate verify
    Change Cipher Spec
    Finished
    Note(s):
    - The client certificate is only sent when the CSMS uses security profile 3.
6. The CSMS performs the following actions:
    Change Cipher Spec
    Finished
7. The Test System sends a HTTP upgrade request to the CSMS
    Note(s):
    - The HTTP request only contains a username/password combination when the CSMS uses security profile 2.
8. The CSMS upgrades the connection to a (secured) WebSocket connection.
9. The Test System sends a BootNotificationRequest
    with reason PowerUp
    chargingStation.model <Configured model>
    chargingStation.vendorName <Configured vendorName>
10. The CSMS responds with a BootNotificationResponse
11. The Test System notifies the CSMS about the current state of all connectors.
    Message: StatusNotificationRequest
    - connectorStatus Available
    Message: NotifyEventRequest
    - trigger Delta
    - actualValue "Available"
    - component.name "Connector"
    - variable.name "AvailabilityState"
12. The CSMS responds accordingly.

Tool validations
* Step 10:
    Message: BootNotificationResponse
    - status Accepted

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
