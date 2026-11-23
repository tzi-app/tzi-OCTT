"""
Test case name      Stop Transaction with a Master Pass - Without UI
Test case Id        TC_C_49_CSMS
Use case Id(s)      C16
Requirement(s)      C16_FR_02

Requirement Details:
    C16.FR.02: The Charging Station SHALL stop all ongoing transactions as described in use case E07.
        Precondition: User presents an IdToken that has a groupId equal to MasterPassGroupId AND the Charging
                      Station does NOT have a UI.
System under test   CSMS

Description         This test case covers how somebody with a Master Pass (User) can stop (selected) ongoing
                    transactions, so the cable becomes unlocked. This Master Pass can be configured in:
                    MasterPassGroupId. This could for example be usefull for Law Enforcement officials.

Purpose             To verify if the CSMS is able to correctly respond on a request to stop all transactions
                    when an idToken which has the MasterPass as GroupId is used and the Charging Station does
                    not have a User Interface according to the mechanism as described in the OCPP
                    specification.

Prerequisite(s)     - N/a

Configuration State N/a

Memory State        An idToken with the MastersPass as GroupId is configured

Reusable State(s)   State is EnergyTransferStarted for EVSE 1 with idToken valid idToken
                    State is EnergyTransferStarted for EVSE 2 with idToken valid idToken2

Test Scenario
1. The Test System sends an AuthorizeRequest with
    - idToken.idToken <Configured masterpass_idtoken_idtoken>
    - idToken.type <Configured masterpass_idtoken_type>
2. The CSMS responds with an AuthorizeResponse
3. The Test System sends a TransactionEventRequest with
    - transactionInfo.stoppedReason MasterPass
    - idToken.idToken <Configured valid_idtoken_idtoken>
    - idToken.type <Configured valid_idtoken_type>
    - eventType Ended
    for both EVSE
4. The CSMS responds with a TransactionEventResponse
    for both EVSE

Tool validations
* Step 2:
    Message AuthorizeResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>
* Step 4:
    Message TransactionEventResponse
    - idTokenInfo.status Accepted
    - idTokenInfo.groupIdToken.idToken <Configured masterPassGroupId>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.1. Page 1022 - 1024 - (2026-04) - TC_C_47_CSMS/TC_C_48_CSMS/TC_C_49_CSMS - Removed configuration
        variable masterPassGroupId
        The <Configured MasterPassGroupId> variable has been removed from the OCTT. The MasterPassGroupId can
        be provided to the OCTT by the CSMS through a SetVariableRequest.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Manual action : trigger CSMS to set the masterPassGroupId | |
        | 2. The Charging Station responds with SetVariablesResponse with attributeStatus = Accepted | 1. Test
          System sends SetVariablesRequest with: / - variable.name = "MasterPassGroupId" / - component.name =
          "AuthCtrlr" / - attributeValue = <Specified masterPassGroupId> |

        Where applicable tool validations mentioning <Configured masterPassGroupId> were replace with the
        masterPassGroupId specified through the SetVariablesRequest

        | Tool validations |
        | \\* Step 4: / Message AuthorizeResponse / - idTokenInfo.groupIdToken.idToken [removed: <Configured
          masterPassGroupId>] <masterPassGroupId from step 1> / \\* Step 6: / Message TransactionEventResponse
          / - idTokenInfo.groupIdToken.idToken [removed: <Configured masterPassGroupId>] <masterPassGroupId
          from step 1> |
        | Post scenario validations: / - N/a |
"""
