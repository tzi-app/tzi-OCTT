"""
Test case name      Set Variables - multiple values
Test case Id        TC_B_10_CSMS
Use case Id(s)      B05
Requirement(s)      B05.FR.01, B05.FR.02, B05.FR.03

Requirement Details:
    B05.FR.01: The Charging Station SHALL respond with an SetVariablesResponse with an equal (X) number of
               SetVariableResult elements, one for every SetVariableData element in the SetVariablesRequest.
        Precondition: When the Charging Station receives a SetVariablesRequest with an X number of
                      SetVariableData elements
    B05.FR.02: Every SetVariableResult element in the SetVariablesResponse SHALL contain the same component
               and variable combination as one of the SetVariableData elements in the SetVariablesRequest.
        Precondition: B05.FR.01
    B05.FR.03: The corresponding SetVariableResult element in the SetVariablesResponse SHALL also contain the
               same attributeType
        Precondition: B05.FR.02 AND If the SetVariablesRequest contains an attributeType
System under test   CSMS

Description         Set the value of two of the required variables of OCPPCommCtrlr

Purpose             To test setting multiple values using SetVariablesRequest for one of the mandatory
                    component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. (CSMS) Manually request CSMS to set data for:
    - OCPPCommCtrlr.OfflineThreshold
    - AuthCtrlr.AuthorizeRemoteStart+
2. (Charging Station) Test System responds with: SetVariablesResponse

Tool validations
* Step 1:
    Message: SetVariablesRequest with (in arbitraty order):
    setVariableData[1]:
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = "123"
    - attributeType is absent or attributeType = Actual
    setVariableData[2]:
    - variable.name = "AuthorizeRemoteStart"
    - component.name = "AuthCtrlr"
    - attributeValue = "false"
    - attributeType is absent or attributeType = Actual

Post scenario validations:
    Manually validate that CSMS has correctly set the requested variables.
"""
