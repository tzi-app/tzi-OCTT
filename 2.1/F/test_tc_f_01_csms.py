"""
Test case name      Remote start transaction - Cable plugin first
Test case Id        TC_F_01_CSMS
Use case Id(s)      F01
Requirement(s)      N/a
System under test   CSMS

Description         OCPP 2.x.x allows an EV driver to either first connect the EV and EVSE OR wait for/trigger
                    a RequestStartTransactionRequest. Both sequences will result in being able to charge.

Purpose             To verify if the CSMS is able to handle a Charging Station that is starts a charging
                    session when the EV driver first connects the EV and EVSE, before receiving a
                    RequestStartTransactionRequest message.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
Manual Action: Trigger the CSMS to request the Charging Station to start a transaction.

1. The CSMS sends a RequestStartTransactionRequest
2. The Test System responds with a RequestStartTransactionResponse
    - with status Accepted
    - transactionId is <Generated transactionId>
3. The Test System sends a TransactionEventRequest.
    - with triggerReason is RemoteStart
    - transactionInfo.remoteStartId is <By CSMS provided remoteStartID>
    - eventType is Updated
4. The CSMS responds with a TransactionEventResponse.
5. Execute Reusable State EnergyTransferStarted (State is Authorized and _EVConnected = true)

Tool validations
* Step 1:
    Message: RequestStartTransactionRequest
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>

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
