"""
Test case name      Reset EVSE - With Ongoing Transaction - OnIdle
Test case Id        TC_B_26_CSMS
Use case Id(s)      B12
Requirement(s)      B12.FR.07

Requirement Details:
    B12.FR.07: The transaction on the EVSE SHALL be terminated normally, before the reset, e.g. as in E06 -
               Stop Transaction.
        Precondition: If an evseId is supplied AND If a transaction is in progress on the EVSE and an OnIdle
                      reset is received.
System under test   CSMS

Description         This test case covers how the CSMS can remotely request the Charging Station to reset an
                    EVSE by sending a ResetRequest during a transaction. When ResetRequest "OnIdle" is send
                    the charging stations schedules a reboot after all transactions are stopped.

                    This could for example be necessary if the Charging Station is not functioning correctly.

Purpose             To verify if the CSMS is able to perform the reset mechanism as described at the OCPP
                    specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EnergyTransferStarted

Test Scenario
Manual Action: Request the CSMS to reboot the charging EVSE with status OnIdle

1. The CSMS sends a ResetRequest
    with status OnIdle
    and evseID <Configured evseId>
2. The Test System responds with a ResetResponse
    with status Scheduled
3. The Test System sends a TransactionEventRequest.
    - eventType Updated
    - triggerReason StopAuthorized
    - transactionInfo.chargingState EVConnected
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
4. The CSMS responds with a TransactionEventResponse.
5. The Test System sends a TransactionEventRequest.
    - eventType Ended
    - triggerReason EVCommunicationLost
    - transactionInfo.chargingState Idle
    - transactionInfo.stoppedReason EVDisconnected
6. The CSMS responds with a TransactionEventResponse.

Tool validations
* Step 1:
    Message ResetRequest
    - type OnIdle
    - evseId <Configured evseId>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.5. Page 82 - (2026-04) - B12 - Reset with ongoing transaction allows wait for cable disconnection
        (Part 2 errata - applies to this test via use case B12)
        New requirements have been added to clarify the expected behavior when a reset is requested during an
        ongoing transaction, including the requirement to allow waiting for cable disconnection before
        performing the reset. Requirements were further updated for clarity.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | B12.FR.11 | B12.FR.03 AND / The transaction(s) on the EVSE(s) are terminated | The Charging Station
          MAY wait for cable disconnection before initiating a reboot | |
        | B12.FR.12 | B12.FR.07 AND / The transaction on the EVSE is terminated | The Charging Station MAY
          wait for cable disconnection before initiating a reset of the EVSE | |
        | B12.FR.13 | B12.FR.11 | The Charging Station SHALL reboot | |
        | B12.FR.14 | B12.FR.12 | The Charging Station SHALL reset the EVSE | |

        Changed requirement

        | | ID | Precondition | Requirement definition | Note |
        | Old | B12.FR.01 | When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Scheduled), [removed: to indicate
          whether the Charging Station will attempt to reset itself or EVSE after all transactions on Charging
          Station or EVSE have ended.] | |
        | New | B12.FR.01 | When the Charging Station receives a ResetRequest(OnIdle) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Scheduled) | |
        | Old | B12.FR.02 | When the Charging Station receives a ResetRequest(Immediate) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Accepted), [removed: to indicate
          whether the Charging Station will attempt to reset itself or EVSE.] | |
        | New | B12.FR.02 | When the Charging Station receives a ResetRequest(Immediate) AND a transaction is
          ongoing | The Charging Station SHALL respond with a ResetResponse(Accepted) | |

        | | ID | Precondition | Requirement definition | Note |
        | Old | B12.FR.03 | If no evseId is supplied / [removed: AND] / [removed: If any transaction is in
          progress and an OnIdle reset is received.] | The transaction of the Charging Station SHALL be
          terminated normally, before the reboot, e.g. as in E06 - Stop Transaction. | |
        | New | B12.FR.03 | B12.FR.01 AND / If no evseId is supplied | The transaction of the Charging Station
          SHALL be terminated normally, before the reboot, e.g. as in E06 - Stop Transaction. | |
        | Old | B12.FR.04 | If no evseId is supplied / [removed: AND] / [removed: If any transaction is in
          progress and an Immediate Reset is received.] | The Charging Station SHALL attempt to terminate any
          transaction in progress and send a TransactionEventRequest (eventType = Ended) message with
          triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset for each terminated
          transaction before performing a reboot. | |
        | New | B12.FR.04 | B12.FR.02 AND / If no evseId is supplied | The Charging Station SHALL attempt to
          terminate any transaction in progress and send a TransactionEventRequest (eventType = Ended) message
          with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset for each
          terminated transaction before performing a reboot. | |
        | Old | B12.FR.05 | [removed: If an Immediate Reset without evseId is received and] the
          TransactionEventResponse is not received within timeout. | The Charging Station SHALL queue the
          TransactionEventRequest, reboot and resend the TransactionEventRequest after the reboot. | |
        | New | B12.FR.05 | B12.FR.04 AND / the TransactionEventResponse is not received within timeout. | The
          Charging Station SHALL queue the TransactionEventRequest, reboot and resend the
          TransactionEventRequest after the reboot. | |
        | Old | B12.FR.07 | If an evseId is supplied / [removed: AND] / [removed: If a transaction is in
          progress on the EVSE and an OnIdle reset is received.] | The transaction on the EVSE SHALL be
          terminated normally, before the reset, e.g. as in E06 - Stop Transaction. | |
        | New | B12.FR.07 | B12.FR.01 AND / If an evseId is supplied | The transaction on the EVSE SHALL be
          terminated normally, before the reset, e.g. as in E06 - Stop Transaction. | |
        | Old | B12.FR.08 | If an evseId is supplied / [removed: AND] / [removed: If a transaction is in
          progress on the EVSE and an Immediate Reset is received.] | The Charging Station SHALL attempt to
          terminate the transaction in progress on the EVSE and send a TransactionEventRequest (eventType =
          Ended) message with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset
          before resetting the EVSE. | |
        | New | B12.FR.08 | B12.FR.02 AND / If an evseId is supplied | The Charging Station SHALL attempt to
          terminate the transaction in progress on the EVSE and send a TransactionEventRequest (eventType =
          Ended) message with triggerReason = ResetCommand and transactionInfo.stoppedReason = ImmediateReset
          before resetting the EVSE. | |
"""
