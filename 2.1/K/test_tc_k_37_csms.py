"""
Test case name      Remote start transaction with charging profile - Success
Test case Id        TC_K_37_CSMS
Use case Id(s)      K05,F01
Requirement(s)      K05.FR.02, F01.FR.08, F01.FR.09, F01.FR.11

Requirement Details:
    K05.FR.02: The Purpose of the ChargingProfile SHALL always be TxProfile.
        Precondition: K05.FR.01
    F01.FR.08: The CSMS MAY include a ChargingProfile in the RequestStartTransactionRequest.
    F01.FR.09: The purpose of this ChargingProfile SHALL be set to TxProfile.
        Precondition: F01.FR.08
    F01.FR.11: The transactionId in the ChargingProfile SHALL NOT be set.
        Precondition: F01.FR.08
System under test   CSMS

Description         The CSMS sets a TxProfile on a specific EVSE inside a RequestStartTransactionRequest
                    message.

Purpose             To verify if the CSMS is able to set a TxProfile on a specific EVSE in a
                    RequestStartTransactionRequest message.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse
    - With status Accepted
3. The Test System sends a TransactionEventRequest With
    - triggerReason RemoteStart
    - transactionInfo.remoteStartId is present.
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 1:
    Message: RequestStartTransactionRequest
    - idToken.idToken <Configured valid idToken>
    - idToken.type <Configured valid idToken type>
    - evseId <Configured evseId>
    - chargingProfile contains:
    - chargingProfile.chargingProfilePurpose is TxProfile
    - chargingProfile.transactionId is omitted
    - chargingProfile.chargingProfileKind is Relative OR Absolute
    - If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
    - If chargingProfileKind is Absolute then chargingSchedule.startSchedule must NOT be omitted.

    The received Charging Profile must comply with the requirements defined at part 2 specification.

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.13. Page 227 - (2026-06) - New F01.FR.27 and F02.FR.28 for evseId in RequestStartTransactionRequest
        [1281]
        (Part 2 errata - applies to this test via use case F01)
        There has always been an implicit (silent) requirement that a CSMS is able to provide an EVSE ID in a
        RequestStartTransactionRequest. It is only for flexibility that the option was given to let the
        charging station decide which EVSE to use if it is able to do so. A charging station that cannot do
        this can reject the request. In that case CSMS will have to send a new RequestStartTransaction with an
        EVSE ID.

        Unfortunately, due to the evseId being an optional field, a CSMS could be implemented that is never
        sending an evseId and still comply to the requirements. Therefore, a new requirement is added to close
        this gap.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | F01.FR.27 |  | CSMS SHALL be able to provide an evseId in a RequestStartTransactionRequest for
          interoperability with Charging Stations that do not accept RequestStartTransactionRequest without
          it. | F01.FR.07 allows a charging station to reject a request without evseId. F01.FR.06 allows CSMS
          to send a request without evseId, but in case of F01.FR.07 it must be able to provide a evseId. |

        The same requirement is also for F02.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | F02.FR.28 |  | CSMS SHALL be able to provide an evseId in a RequestStartTransactionRequest for
          interoperability with Charging Stations that do not accept RequestStartTransactionRequest without
          it. | (Same as F01.FR.27) / F02.FR.15 allows a charging station to reject a request without evseId.
          F02.FR.14 allows CSMS to send a request without evseId, but in case of F02.FR.15 it must be able to
          provide a evseId. |
"""
