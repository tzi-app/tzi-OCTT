"""
Test case name      Set new NetworkConnectionProfile - Add new NetworkConfiguration using SetVariables
Test case Id        TC_B_105_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.29. B09.FR.30

Requirement Details:
    B09.FR.29 (2.1): CSMS SHALL set variable ApnEnabled resp. VpnEnabled of NetworkConfiguration to True.
        Precondition: When CSMS configures variables for an APN or VPN connection
    B09.FR.30 (2.1): CSMS SHALL set variable ApnEnabled resp. VpnEnabled of NetworkConfiguration to False.
        Precondition: When CSMS does not configure variables for an APN or VPN connection
System under test   Charging Station

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify that CSMS can set NetworkConfiguration and correctly sets the value of
                    Apn/VpnEnabled.

Prerequisite(s)     CSMS is able to set the NetworkConfiguration component
                    Test System reports NetworkConfiguration variables as ReadWrite.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: In the following steps <configurationSlot> equals <Configured non-active configurationSlot>
Note: Request CSMS to set a network configuration that includes APN connection details, but no VPN details.

1. CSMS sends a SetVariablesRequest on component NetworkConfiguration[<Configured non-active
   configurationSlot>]
2. The Charging Station responds with SetVariablesResponse(s) with
    - setVariableResult.attributeStatus = Accepted for each variable

Tool validations
* Step 2: (The following can be sent in one or multiple messages.)
    Message SetVariablesRequest for
    component NetworkConfiguration[<Configured non-active configurationSlot>] with:
    - OcppCsmsUrl = <Configured ocppCsmsUrl>
    - OcppInterface = Any
    - OcppTransport = JSON
    - OcppVersion = OCPP21
    - MessageTimeout = <Configured messageTimeout>
    - SecurityProfile = 2
    - Identity = <Configured charging station identity>
    - BasicAuthPassword = PasswordOfSufficientLength
    - VpnEnabled = false
    - ApnEnabled = true
    - Apn = <Configured APN URL>
    - ApnUserName = <Configured APN username>
    - ApnPassword = <Configured APN password>
    - ApnAuthentication one of PAP, CHAP, NONE, AUTO

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.5. Page 1006 - (2026-02) - TC_B_105_CSMS - Manual action added
        The note before step 1. has been changed to indicate a manual action is required.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | [removed: Note: Request CSMS to set a network configuration that includes APN connection details,
          but no VPN details.] | |
        | Manual action : Request CSMS to set a network configuration that includes APN connection details,
          but no VPN details. | |
        | 2. The [removed: Charging Station] Test system responds with / SetVariablesResponse(s) with / -
          setVariableResult.attributeStatus = Accepted for each variable | 1. CSMS sends a SetVariablesRequest
          on component / NetworkConfiguration[<Configured non-active configurationSlot>] |
"""
