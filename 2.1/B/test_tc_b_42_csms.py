"""
Test case name      Set new NetworkConnectionProfile - Accepted
Test case Id        TC_B_42_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.01

Requirement Details:
    B09.FR.01: The Charging Station SHALL validate the content, store the new data and if successful, respond
               by sending a SetNetworkProfileResponse message, with status Accepted
        Precondition: On receipt of the SetNetworkProfileRequest
        Note: Matches B09.FR.33 for NetworkConfiguration.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify if the CSMS is able to set a new network connection profile at one of the by the
                    Charging Station defined configuration slots.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse
    With status Accepted

Tool validations
* Step 1:
    Message SetNetworkProfileRequest
    - configurationSlot is <Configured configurationSlot>
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppCsmsUrl <Configured ocppCsmsUrl>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile>

Post scenario validations:
    - N/a
"""
