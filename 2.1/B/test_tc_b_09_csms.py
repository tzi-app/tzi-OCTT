"""
Test case name      Set Variables - single value
Test case Id        TC_B_09_CSMS
Use case Id(s)      B05
Requirement(s)      B05.FR.01, B05.FR.02, B05.FR.03, B05.FR.10, B05.FR.12

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
    B05.FR.10: The Charging Station SHALL set the attributeStatus field in the corresponding SetVariableResult
               to: Accepted.
        Precondition: When the Charging Station was able to set the given value from the SetVariableData
    B05.FR.12: The corresponding SetVariableResult element in the SetVariablesResponse SHALL contain the
               attributeType Actual.
        Precondition: When the Charging Station receives a SetVariablesRequest without an attributeType.
System under test   CSMS

Description         Set the value of one of the required variables of OCPPCommCtrlr

Purpose             To test setting a single value using SetVariablesRequest for one of the mandatory
                    component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually request CSMS to set data for:
    - OCPPCommCtrlr.OfflineThreshold
2. Test System responds with: SetVariablesResponse

Tool validations
* Step 1:
    Message: SetVariablesRequest with (in arbitraty order):
    setVariableData[1]:
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"
    - attributeValue = "123"
    - attributeType is absent or attributeType = Actual

Post scenario validations:
    Manually validate that CSMS has correctly set the requested variables.
"""
