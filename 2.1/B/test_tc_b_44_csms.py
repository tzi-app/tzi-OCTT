"""
Test case name      Set new NetworkConnectionProfile - Failed
Test case Id        TC_B_44_CSMS
Use case Id(s)      B09
Requirement(s)      B09.FR.03

Requirement Details:
    B09.FR.03: The Charging Station SHALL respond by sending a SetNetworkProfileResponse message, with status
               Failed
        Precondition: If setting a valid NetworkConnectionProfile in a SetNetworkProfileRequest fails.
System under test   CSMS

Description         The CSMS updates the connection details on the Charging Station. For instance in
                    preparation of a migration to a new CSMS.

Purpose             To verify if the CSMS is able to handle a Charging Station responding with status Failed,
                    when setting a new network connection profile at one of the by the Charging Station
                    defined configuration slots.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. The CSMS sends a SetNetworkProfileRequest
2. The Test System responds with a SetNetworkProfileResponse
    - With status Failed

Tool validations
N/a

Post scenario validations:
    - N/a
"""
