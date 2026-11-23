"""
Test case name      Upgrade Charging Station Security Profile - Accepted
Test case Id        TC_A_19_CSMS
Use case Id(s)      A05
Requirement(s)      A05.FR.04, A05.FR.07

Requirement Details:
    A05.FR.04: The Charging Station SHALL respond with SetVariablesResponse(Accepted)
        Precondition: The Charging Station receives SetVariablesRequest for NetworkConfigurationPriority
                      containing profile slots for NetworkConnectionProfiles with a 'securityProfile' value
                      equal to or higher than the current value AND all prerequisites are met
    A05.FR.07: The CSMS SHALL NOT allow the Charging Station to connect with a lower security profile anymore.
        Precondition: A05.FR.06
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station, to increase the security
                    profile level.

Purpose             To verify if the CSMS is able to set a new network connection profile at one of the by the
                    Charging Station defined configuration slots with a higher security profile than currently
                    configured.

Prerequisite(s)     - Security profile must be set to 1 or 2.
                    - If Security profile is set to 1, then a trusted certificate must be installed.

Configuration State N/a

Memory State        If configured <Security profile> is 2, then RenewChargingStationCertificate
                    The Test System uses this certificate during the TLS handshake when connecting with
                    security profile 3.

Reusable State(s)   N/a

Test Scenario
Manual Action: Request the CSMS to set a new NetworkConnectionProfile with a security profile level one higher
               than currently configured

1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse With status Accepted

Manual Action: Request the CSMS to change the NetworkConfigurationPriority to one that contains the
               configurationSlot of the new NetworkConnectionProfile from step 1

3. The CSMS sends a SetVariablesRequest
4. The Test System responds with a SetVariablesResponse with status Accepted

Manual Action: Request the CSMS to reboot the Charging Station

5. The CSMS sends a ResetRequest
6. The Test System responds with a ResetResponse with status Accepted
7. The Test System reconnects to the CSMS using the new NetworkProfile, containing the upgraded security
   profile <Configured securityProfile + 1>.
8. The CSMS accepts the connection attempt.
9. Execute Reusable State Booted
10. The Test System reconnects to the CSMS using the original NetworkProfile, containing the lower security
    profile.
    Note(s):
    - This is done to ensure that the CSMS does not accept a connection using the lower security profile
      anymore.
11. The CSMS shall not accept the connection attempt.
12. The Test System reconnects to the CSMS using the new NetworkProfile, containing the upgraded security
    profile <Configured securityProfile + 1>.
    Note(s):
    - This is done to restore the connection before ending the testcase.
13. The CSMS accepts the connection attempt.

Tool validations
* Step 1:
    Message SetNetworkProfileRequest
    - connectionData.messageTimeout <Configured messageTimeout>
    - connectionData.ocppInterface <Configured ocppInterface>
    - connectionData.ocppTransport JSON
    - connectionData.ocppVersion OCPP20
    - connectionData.securityProfile <Configured securityProfile + 1>
* Step 3:
    Message SetVariablesRequest
    setVariableData:
    - variable.name = "NetworkConfigurationPriority"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = <contains configurationSlot provided at step 1>
* Step 11:
    When upgrading a Charging Station to a higher security profile, a CSMS has several options regarding which
    endpoint to use. This affects the way the CSMS is able to detect it needs to reject the incoming
    connection attempt.

    In case of having upgraded from security profile 2 to 3, but there is an incoming connection attempt using
    security profile 2:
    When the same endpoint is used, then it depends on the CSMS endpoint configuration.
    - When the CSMS does a full switch and only allows TLS handshakes when a client certificate is provided,
      then the TLS handshake is rejected.
    - When the CSMS only requires this Charging Station to use a client certificate, then it accepts the TLS
      handshake (because it will be unable to detect which Charging Station is connecting) and it rejects the
      HTTP request to establish the WebSocket connection.

    When a different port or a whole different endpoint is used for the upgrade, then on the original endpoint
    the CSMS accepts the TLS handshake and it rejects the HTTP request to establish the WebSocket connection
    (because this Charging Station is not allowed to connect with security profile 2 anymore).

    In case of security profile 1, the case is always the same. The CSMS shall always reject the HTTP request
    to establish the WebSocket connection, because TLS is required for this Charging Station.

Post scenario validations:
    The Test System and the CSMS are connected.
"""
