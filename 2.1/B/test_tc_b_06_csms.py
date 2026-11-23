"""
Test case name      Get Variables - single value
Test case Id        TC_B_06_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.01, B06.FR.02, B06.FR.03, B06.FR.04, B06.FR.10, B06.FR.11

Requirement Details:
    B06.FR.01: The Charging Station SHALL respond with an GetVariablesResponse with an equal (X) number of
               GetVariableResult elements, one for every GetVariableData element in the GetVariablesRequest.
        Precondition: When the Charging Station receives a GetVariablesRequest with an X number of
                      GetVariableData elements
    B06.FR.02: Every GetVariableResult element in the GetVariablesResponse SHALL contain the same component
               and variable combination as one of the GetVariableData elements in the GetVariablesRequest.
        Precondition: B06.FR.01
    B06.FR.03: The corresponding GetVariableResult element in the GetVariablesResponse SHALL also contain the
               same attributeType
        Precondition: B06.FR.02 AND If the GetVariablesRequest contains an attributeType
    B06.FR.04: Every GetVariableResult element in the GetVariablesResponse SHALL contain an attributeValue
               with the value of an attribute from the requested attributeType in the GetVariablesRequest.
        Precondition: B06.FR.01
    B06.FR.10: The Charging Station SHALL set the attributeStatus field in the corresponding GetVariableResult
               to: Accepted and set the attributeValue to the found value.
        Precondition: When the Charging Station was able to get the value requested from a GetVariablesRequest
    B06.FR.11: The corresponding GetVariableResult element in the GetVariablesResponse SHALL contain the
               attributeType Actual.
        Precondition: When the Charging Station receives a GetVariablesRequest without an attributeType.
System under test   CSMS

Description         Get the value of two of the required variables of OCPPCommCtrlr

Purpose             To test getting single value using GetVariablesRequest for one of the
                    mandatory component/variable combinations that must exist in the DM implementation.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually request CSMS to get data for:
    - OCPPCommCtrlr.OfflineThreshold
2. Test System responds with: GetVariablesResponse

Tool validations
* Step 1:
    Message: GetVariablesRequest with (in arbitrary order)
    getVariableData[0]:
    - attributeType is at least absent or attributeType = Actual, but Target, MinSet, and MaxSet are also
      allowed
    - variable.name = "OfflineThreshold"
    - component.name = "OCPPCommCtrlr"

Post scenario validations:
    Manually validate that CSMS has correctly read the requested variables.
"""
