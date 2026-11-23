"""
Test case name      Get Variables - limit to maximum number of values
Test case Id        TC_B_08_CSMS
Use case Id(s)      B06
Requirement(s)      B06.FR.05

Requirement Details:
    B06.FR.05: The CSMS SHALL NOT send more GetVariableData elements in a GetVariablesRequest than reported by
               the Charging Station via ItemsPerMessageGetVariables.
System under test   CSMS

Description         Do not request more variables than supported by MaxItemsPerMessageGetVariables.

Purpose             To test that CSMS does not request more variables than the Charging Station reported to
                    support in the variable MaxItemsPerMessageGetVariables.

Prerequisite(s)     N/a

Configuration State Configure (using getVariablesRequest) Component.Variable.Instance
                    DeviceDataCtrlr.ItemsPerMessage.GetVariables at value 4.

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Manually request CSMS for 5 variables:
    - DeviceDataCtrlr.ItemsPerMessage[ GetReport ]
    - DeviceDataCtrlr.ItemsPerMessage[ GetVariables ]
    - DeviceDataCtrlr.BytesPerMessage[ GetReport ]
    - DeviceDataCtrlr.BytesPerMessage[ GetVariables ]
    - AuthCtrlr.AuthorizeRemoteStart
2. Test System responds with GetVariablesResponse with with a list of 4 GetVariableResultType items and a
   GetVariableResponse with 1 GetVariableResultType item.

Tool validations
* Step 1:
    Message: GetVariablesRequest for 4 variables and a GetVariablesRequest for 1 variable (in arbritrary
             order):
    for component.name = "DeviceDataCtrlr"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetReport"
    - variable.name = "ItemsPerMessage" with variable.instance = "GetVariables"
    - variable.name = "BytesPerMessage" with variable.instance = "GetReport"
    - variable.name = "BytesPerMessage" with variable.instance = "GetVariables"
    and for component.name = "AuthCtrlr"
    - variable.name = "AuthorizeRemoteStart"

Post scenario validations:
    Test System validates that not more than ItemsPerMessageGetVariables elements are requested in one
    GetVariablesRequest message by CSMS.
"""
