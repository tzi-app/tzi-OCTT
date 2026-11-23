"""
Test case name      Set new NetworkConnectionProfile - Identity and password
Test case Id        TC_B_100_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.01, B09.FR.14

Requirement Details:
    B09.FR.01: The Charging Station SHALL validate the content, store the new data and if successful, respond
               by sending a SetNetworkProfileResponse message, with status Accepted
        Precondition: On receipt of the SetNetworkProfileRequest
        Note: Matches B09.FR.33 for NetworkConfiguration.
    B09.FR.14 (2.1): CSMS SHOULD use the SetNetworkProfileRequest to set the Identity or BasicAuthPassword of
                     the Charging Station.
        Note: Alternatively the NetworkConfiguration component can be used, if the corresponding variables are
              writable. See requirements from the "NetworkConfiguration" section below.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify if the CSMS is able to set a new network connection profile that contains
                    basicAuthPassword and identity at one of the by the Charging Station defined configuration
                    slots.

Prerequisite(s)     CSMS uses the SetNetworkProfileRequest to update a network connection profile.

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Note: Request CSMS to send a network profile including identity and password.

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
    - connectionData.identity <Configured identity>
    - connectionData.basicAuthPassword <Configured basicAuthPassword>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.6. Page 1002 - (2026-02) - TC_B_100_CSMS - Manual action added and tool validations updated
        The note was replaced with a manual action and tool validations were updated.

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | [removed: Note: Request CSMS to send a network profile including identity and password.] / Manual
          Action : Request CSMS to send a network profile including identity and password. | |

        | Tool validations |
        | \\* Step 1: / Message SetNetworkProfileRequest / - configurationSlot is <Configured
          configurationSlot> / - connectionData.messageTimeout <Configured messageTimeout> / -
          connectionData.ocppCsmsUrl <Configured ocppCsmsUrl> / - connectionData.ocppInterface <Configured
          ocppInterface> / - connectionData.ocppTransport JSON / - connectionData.ocppVersion [removed:
          OCPP20] OCPP21 / - connectionData.securityProfile [removed: <Configured securityProfile>] <Active
          securityProfile> / - connectionData.identity <Configured identity> / -
          connectionData.basicAuthPassword <Configured basicAuthPassword> |
"""
