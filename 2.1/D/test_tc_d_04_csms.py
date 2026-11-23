"""
Test case name      Send Local Authorization List - Full with empy list
Test case Id        TC_D_04_CSMS
Use case Id(s)      D01
Requirement(s)      D01_FR_01, D01_FR_06, D01_FR_18

Requirement Details:
    D01.FR.01: SendLocalListRequest SHALL contain the type of update (updateType) and a version number
               (versionNumber) that the Charging Station MUST associate with the Local Authorization List
               after it has been updated.
    D01.FR.06: All IdTokens in the Local Authorization List SHALL be unique.
        Note: No duplicate values are allowed.
    D01.FR.18: versionNumber in a SendLocalListRequest SHALL be greater than 0.
        Note: In GetLocalListVersionResponse the versionNumber = 0 has a special meaning: No Local List
              installed. So the value 0 should never be used.
System under test   CSMS

Description         The CSMS sends a Local Authorization List which a Charging Station can use for the
                    authorization of idTokens. The list MAY be either a full list to replace the current list
                    in the Charging Station or it MAY be a differential list with updates to be applied to the
                    current list in the Charging Station.

Purpose             To verify if the CSMS is able to send a Full Local Authorization List without data
                    according to the mechanism as described in the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a Local Authorization list to the Charging Station with type full and
               without AuthorizationData elements in the message

1. The CSMS sends a SendLocalListRequest
2. The Test System responds with a SendLocalListResponse with status Accepted

Note(s): If the Local Authorization List is too big for one message, step 1 and 2 will be repeated

Tool validations
* Step 1:
    Message SendLocalListRequest
    - updateType Full
    - localAuthorizationList <Empty>

Post scenario validations:
    - N/a
"""
