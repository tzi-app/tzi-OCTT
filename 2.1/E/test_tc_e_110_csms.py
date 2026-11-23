"""
Test case name      Transactions with fixed cost, energy or time - CSMS specifies energy limit
Test case Id        TC_E_110_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.02

Requirement Details:
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
System under test   CSMS

Description         CSMS will set an energy limit on the transaction.

Purpose             To verify whether the CSMS is able to set an energy limit.

Prerequisite(s)     - CSMS supports setting energy limits
                    - Test System has TxCtrlr.SupportedLimits containing maxEnergy

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
1. The Test System sends a TransactionEventRequest with
    - With eventType is Started
    - triggerReason is ChargingStateChanged
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.chargingState is Charging
    - transactionInfo.transactionLimit <omitted>
2. The CSMS responds with a TransactionEventResponse
3 The Test System sends a TransactionEventRequest with
    - triggerReason is LimitSet
    - transactionInfo.transactionLimit.maxEnergy is <Configured energy limit>
4 The CSMS responds with TransactionEventResponse
5. The Test System sends a TransactionEventRequest with
    - eventType is Updated
    - triggerReason is EnergyLimitReached
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.transactionLimit.maxEnergy <Configured energy limit>
    - transactionInfo.transactionLimit.maxTime <omitted>
    - transactionInfo.transactionLimit.maxCost <omitted>
    - transactionInfo.chargingState SuspendedEVSE
6. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
    - transactionLimit.maxEnergy must be <Configured energy limit>
    - transactionLimit.maxTime must be <omitted>
    - transactionLimit.maxCost must be <omitted>
* Step 4:
    Message: TransactionEventResponse
    - transactionLimit must be <omitted>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.12. Page 1094/1095 - (2026-02) - TC_E_110_CSMS - Added missing Authorization request to initiate
        transaction
        An explicit authorization request was introduced for improved clarity, and the configured energy limit
        was standardized to a fixed value.

        | Test case name | Transactions with fixed cost, energy or time - CSMS specifies energy limit |
        | Test case Id | TC_E_110_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends an AuthorizeRequest / With idToken.idToken <Configured
          valid_idtoken_idtoken> / idToken.type <Configured valid_idtoken_type> | 2. The CSMS responds with an
          AuthorizeResponse |
        | Manual action : In CSMS, configure energy limit of 10000 (Wh) for this transaction | |
        | [removed: 1.] 3. The Test System sends a TransactionEventRequest with / [removed: With] eventType is
          Started / triggerReason is ChargingStateChanged / idToken.idToken <Configured valid_idtoken_idtoken>
          / idToken.type <Configured valid_idtoken_type> / evse.id is <Configured evseId> / evse.connectorId
          is <Configured connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.chargingState is Charging / transactionInfo.transactionLimit <omitted> | [removed:
          2.] 4. The CSMS responds with a TransactionEventResponse |
        | [removed: 3.] 5. The Test System sends a TransactionEventRequest with / triggerReason is LimitSet /
          transactionInfo.transactionLimit.maxEnergy is [removed: <Configured energy limit>] 10000 | [removed:
          4.] 6. The CSMS responds with TransactionEventResponse |
        | [removed: 5.] 7. The Test System sends a TransactionEventRequest with / eventType is Updated /
          triggerReason is EnergyLimitReached / evse.id is <Configured evseId> / evse.connectorId is
          <Configured connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.transactionLimit.maxEnergy [removed: <Configured energy limit>] 10000 /
          transactionInfo.transactionLimit.maxTime <omitted> / transactionInfo.transactionLimit.maxCost
          <omitted> / transactionInfo.chargingState SuspendedEVSE | [removed: 6.] .8 The CSMS responds with a
          TransactionEventResponse |

        | Tool validations |
        | \\* Step [removed: 2] 4: / Message: TransactionEventResponse / idTokenInfo.status must be Accepted /
          transactionLimit.maxEnergy must be [removed: <Configured energy limit>] 10000 /
          transactionLimit.maxTime must be <omitted> / transactionLimit.maxCost must be <omitted> /  / \\* Step
          [removed: 4] 6: / Message: TransactionEventResponse / transactionLimit must be <omitted> |
        | Post scenario validations: / N/a |
"""
