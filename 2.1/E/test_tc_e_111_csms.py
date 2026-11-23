"""
Test case name      Transactions with fixed cost, energy or time - CSMS specifies time limit
Test case Id        TC_E_111_CSMS
Use case Id(s)      E16
Requirement(s)      E16.FR.02

Requirement Details:
    E16.FR.02: CSMS SHALL include the field transactionLimit once in the first possible
               TransactionEventResponse message.
        Precondition: When CSMS sets or changes a limit to the transaction in cost, energy, SoC or time
        Note: transactionLimit uses maxCost for cost limit, maxEnergy for energy limit, maxTime for time limit
              or maxSoC for SoC limit.
System under test   CSMS

Description         CSMS will set a time limit on the transaction.

Purpose             To verify whether the CSMS is able to set a time limit.

Prerequisite(s)     - CSMS supports setting energy limits
                    - Test System has TxCtrlr.SupportedLimits containing maxTime

Configuration State N/a

Memory State        N/a

Reusable State(s)   State is EVConnectedPreSession

Test Scenario
Manual action: In CSMS, configure time limit of duration <Configured time limit> for this transaction

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
3. The Test System sends a TransactionEventRequest with
    - eventType is Updated
    - triggerReason is LimitSet
    - evse.id is <Configured evseId>
    - evse.connectorId is <Configured connectorId>
    - transactionInfo.transactionId is <transactionId>
    - transactionInfo.transactionLimit.maxEnergy <omitted>
    - transactionInfo.transactionLimit.maxTime <Configured time limit>
    - transactionInfo.transactionLimit.maxCost <omitted>
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2:
    Message: TransactionEventResponse
    - idTokenInfo.status must be Accepted
    - transactionLimit.maxEnergy must be <omitted>
    - transactionLimit.maxTime must be <Configured time limit>
    - transactionLimit.maxCost must be <omitted>
* Step 4:
    Message: TransactionEventResponse
    - transactionLimit must be <omitted>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.13. Page 1096/1097 - (2026-02) - TC_E_111_CSMS - Added missing Authorization request to initiate
        transaction
        An explicit authorization request was introduced for improved clarity, and the configured time limit
        was standardized to a fixed value.

        | Test case name | Transactions with fixed cost, energy or time - CSMS specifies time limit |
        | Test case Id | TC_E_111_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | 1. The Test System sends an AuthorizeRequest / With idToken.idToken <Configured
          valid_idtoken_idtoken> / idToken.type <Configured valid_idtoken_type> | 2. The CSMS responds with an
          AuthorizeResponse |
        | Manual action: In CSMS, configure time limit of duration [removed: <Configured time limit>] 120 for
          this transaction | |
        | [removed: 1.] 3. The Test System sends a TransactionEventRequest with / With eventType is Started /
          triggerReason is ChargingStateChanged / idToken.idToken <Configured valid_idtoken_idtoken> /
          idToken.type <Configured valid_idtoken_type> / evse.id is <Configured evseId> / evse.connectorId is
          <Configured connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.chargingState is Charging / transactionInfo.transactionLimit <omitted> | [removed:
          2.] 4. The CSMS responds with a TransactionEventResponse |
        | [removed: 3.] 5. The Test System sends a TransactionEventRequest with / eventType is Updated /
          triggerReason is LimitSet / evse.id is <Configured evseId> / evse.connectorId is <Configured
          connectorId> / transactionInfo.transactionId is <transactionId> /
          transactionInfo.transactionLimit.maxEnergy <omitted> / transactionInfo.transactionLimit.maxTime
          [removed: <Configured time limit>] 120 / transactionInfo.transactionLimit.maxCost <omitted> |
          [removed: 4.] 6. The CSMS responds with a TransactionEventResponse |

        | Tool validations |
        | * Step [removed: 2] 4: / Message: TransactionEventResponse / idTokenInfo.status must be Accepted /
          transactionLimit.maxEnergy must be <omitted> / transactionLimit.maxTime must be [removed:
          <Configured time limit>] 120 / transactionLimit.maxCost must be <omitted> / * Step [removed: 4] 6: /
          Message: TransactionEventResponse / transactionLimit must be <omitted> |
        | Post scenario validations: / N/a |
"""
