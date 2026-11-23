"""
Test case name      Get Local List Version - No list available
Test case Id        TC_D_09_CSMS
Use case Id(s)      D02
Requirement(s)      N/a
System under test   CSMS

Description         The CSMS can request a Charging Station for the version number of the Local Authorization
                    List by sending a GetLocalListVersionRequest.

Purpose             To verify if the CSMS is able to request the Local Authorization List version according to
                    the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to get a Local Authorization list version

1. The CSMS sends a GetLocalListVersionRequest
2. The Test System responds with a GetLocalListVersionResponse with versionNumber 0

Tool validations
- N/a

Post scenario validations:
    - N/a
"""
