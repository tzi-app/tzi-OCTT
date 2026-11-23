"""
Test case name      Basic Authentication - Valid username/password combination
Test case Id        TC_A_01_CSMS
Use case Id(s)      A00, B01
Requirement(s)      A00.FR.204, B01.FR.02

Requirement Details:
    A00.FR.204: The username SHALL be equal to the Charging Station identity, which is the identifying string
                of the Charging Station as it uses it in the OCPP-J connection URL. When using Basic
                Authentication, the Charging Station identity may not contain the character ":". Otherwise the
                CSMS may be unable to separate the username from the password.
        Precondition: A00.FR.203
    B01.FR.02: The CSMS SHALL respond to indicate whether it will accept the Charging Station.
        Precondition: B01.FR.01 The CSMS has received BootNotificationRequest from the Charging Station.
System under test   CSMS

Description         The Charging Station uses Basic authentication to authenticate itself to the CSMS, when
                    using security profile 1 or 2.

Purpose             To verify whether the CSMS is able to validate the (valid) Basic authentication
                    credentials provided by the Charging Station at the connection request.

Prerequisite(s)     The CSMS supports security profile 1 and/or 2

Configuration State The CSMS must have a password configured that equals the configured BasicAuthPassword at
                    the Test System.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The Test System sends a HTTP upgrade request with an Authorization header, containing a username/password
   combination.
    Note(s):
    - The Authorization header is formatted as follows:
      AUTHORIZATION: Basic <Base64 encoded(<Configured ChargingStationId>:<Configured BasicAuthPassword>)>
2. The CSMS validates the username/password combination AND upgrades the connection to a (secured) WebSocket
   connection.
3. The Test System sends a BootNotificationRequest
4. The CSMS responds with a BootNotificationResponse
5. The Test System notifies the CSMS about the current state of all connectors.
6. The CSMS responds accordingly.

Tool validations
* Step 4:
    Message: BootNotificationResponse
    - status must be Accepted

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
