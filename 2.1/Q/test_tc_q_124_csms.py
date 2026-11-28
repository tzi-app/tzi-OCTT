"""
Test case name      Local V2X control for load balancing - good flow
Test case Id        TC_Q_124_CSMS
Use case Id(s)      Q09
Requirement(s)      …
System under test   CSMS

Description         To allow the EV to be utilized for locally controlled load balancing.

Purpose             To verify if the CSMS is able to configure a CS for locally controlled load balancing

Prerequisite(s)     - CSMS supports Bidirectional Power Transfer

Configuration State - CS reports V2XChargingCtrlr.SupportedOperationModes that contains LocalLoadBalancing

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Manual Action: trigger CSMS to set local load-balancing thresholds:
- UpperThreshold = 1000, LowerThreshold = -1000
- UpperOffset = 200, LowerOffset = 0

1. The CSMS sends a SetVariablesRequest
    Note: CSMS may send these variables in one or multiple requests
2. The Test System responds with a SetVariablesResponse with
    - setVariableResult[0].component.name V2XChargingCtrlr
    - setVariableResult[0].component.evse.id 1
    - setVariableResult[0].variable.name V2XLocalLoadBalancing
    - setVariableResult[0].variable.instance UpperThreshold
    - setVariableResult[0].attributeStatus Accepted
    - setVariableResult[1].component.name V2XChargingCtrlr
    - setVariableResult[1].component.evse.id 1
    - setVariableResult[1].variable.name V2XLocalLoadBalancing
    - setVariableResult[1].variable.instance LowerThreshold
    - setVariableResult[1].attributeStatus Accepted
    - setVariableResult[2].component.name V2XChargingCtrlr
    - setVariableResult[2].component.evse.id 1
    - setVariableResult[2].variable.name V2XLocalLoadBalancing
    - setVariableResult[2].variable.instance UpperOffset
    - setVariableResult[2].attributeStatus Accepted
    - setVariableResult[3].component.name V2XChargingCtrlr
    - setVariableResult[3].component.evse.id 1
    - setVariableResult[3].variable.name V2XLocalLoadBalancing
    - setVariableResult[3].variable.instance LowerOffset
    - setVariableResult[3].attributeStatus Accepted

CSMS sets a Charging Profile with LocalLoadBalancing

Manual Action: trigger CSMS to set a TxDefaultProfile Charging Profile with chargingSchedulePeriod with
               operationMode LocalLoadBalancing

3. The CSMS the sends a SetChargingProfileRequest
4. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 1:
    Message SetVariablesRequest with
    - setVariableData[0].component.name V2XChargingCtrlr
    - setVariableData[0].component.evse.id 1
    - setVariableData[0].variable.name V2XLocalLoadBalancing
    - setVariableData[0].variable.instance UpperThreshold
    - setVariableData[0].attributeValue 2000
    - setVariableData[1].component.name V2XChargingCtrlr
    - setVariableData[1].component.evse.id 1
    - setVariableData[1].variable.name V2XLocalLoadBalancing
    - setVariableData[1].variable.instance LowerThreshold
    - setVariableData[1].attributeValue -1000
    - setVariableData[2].component.name V2XChargingCtrlr
    - setVariableData[2].component.evse.id 1
    - setVariableData[2].variable.name V2XLocalLoadBalancing
    - setVariableData[2].variable.instance UpperOffset
    - setVariableData[2].attributeValue 200
    - setVariableData[3].component.name V2XChargingCtrlr
    - setVariableData[3].component.evse.id 1
    - setVariableData[3].variable.name V2XLocalLoadBalancing
    - setVariableData[3].variable.instance LowerOffset
    - setVariableData[3].attributeValue 0
    Note: Alternatively these may be sent as individual requests

* Step 3:
    Message: SetChargingProfileRequest
    - evseId must be <Configured evseId>
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].operationMode must be LocalLoadBalancing
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].limit(_L2/L3) must be _<omitted>_
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].dischargingLimit(_L2/L3) must be
      _<omitted>_
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpoint(_L2/L3) must be _<omitted>_
    - chargingProfile.chargingSchedule[*].chargingSchedulePeriod[*].setpointReactive(_L2/L3) must be
      _<omitted>_

Post scenario validations:
    N/a

Remarks
Transcriber note (not printed in the document): the Requirement(s) cell is printed as "…" with no requirement
codes. The Manual action prints UpperThreshold = 1000, while the Step 1 tool validation prints
setVariableData[0].attributeValue 2000; both are transcribed as printed.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.22. Page 531 - (2026-02) - Use case Q09 has improved description of LocalLoadBalancing
        (Part 2 errata - applies to this test via use case Q09)
        | No. | Type | Description |
        | 1 | Name | Local V2X control for load balancing |
        | 2 | ID | Q09 |
        | 3 | Objective | … |
        | 4 | Description | … |
        |  | Actors | EV, Charging Station, CSMS |

        | No. | Type | Description |
        |  | Scenario description | 1. The CSMS has sent a [setchargingprofilerequest] message, with a
          chargingSchedule that has one or more periods with operationMode set to LocalLoadBalancing. / 2. The
          Charging Station will continually get the latest load power reading to calculate a new setpoint that
          will offset the measured power generation or consumption, such that it stays between the configured
          upper and lower limit. /  / Configuration variables are instances of
          V2XChargingCtrlr.LocalLoadBalancing: / • The upper limit is defined as: UpperThreshold + UpperOffset
          . / • The lower limit is defined as: LowerThreshold + LowerOffset . |
        | 5 | Prerequisites | • Charging Station is able to read the upstream meter. / • The configuration
          variable UpperThreshold (a positive value) should be equal or above the minimum charging rate of the
          EV. / • The configuration variable LowerThreshold (a negative value) should be equal or below the
          minimum (as in "closest to zero") discharging rate of the EV. |
        | 6 | Post conditions | ChargingSchedulePeriod ends |
        | 7 | Error Handling |  |
        | 8 | Remarks | By setting the configuration variable UpperOffset to -UpperThreshold and LowerOffset
          to -LowerThreshold the nett power will be regulated down to 0 W as soon as the building power
          exceeds the thresholds. /  / See section [intro-localloadbalancing] in the introduction of this
          chapter for more detailed information on how local load-balancing works. /  / This use case only
          works for one Charging Station, but can work for multiple EVSEs when Charging Station has the
          capability to combine setpoints from multiple EVSEs to compensate the measured load at the upstream
          meter. /  / Local load-balancing by multiple Charging Stations would have to be coordinated by a
          CSMS or Local Controller using the Central Setpoint use case. |

    2.23. Page 533 - (2026-02) - Use case Q09 has improved sequence diagram
        (Part 2 errata - applies to this test via use case Q09)
        `mermaid
        sequenceDiagram
        participant EV
        participant CS as Charging Station
        participant CSMS
        Note over CS: Transaction has started
        alt 15118-20 Scheduled mode
        Note over EV: Not applicable
        else 15118-20 Dynamic mode
        EV->>CS: ScheduleExchangeReq( DepartureTime, EVTargetEnergyRequest, Dynamic, ... )
        CS->>CSMS: NotifyEVChargingNeedsRequest( DepartureTime, EVTargetEnergyRequest, ... )
        CSMS-->>CS: NotifyEVChargingNeedsResponse( Accepted )
        CSMS->>CS: SetChargingProfileRequest( v2xSchedule "LocalLoadBalancing" )
        CS-->>CSMS: SetChargingProfileResponse( Accepted )
        CS-->>EV: ScheduleExchangeRes()
        EV->>CS: PowerDeliveryReq()
        CS-->>EV: PowerDeliveryRes()
        loop Updating setpoint dynamically every schedule period
        CS->>CS: Get power reading from grid connection
        alt Load - Setpoint < LowerThreshold + LowerOffset - UpperThreshold
        CS->>CS: Setpoint_new = Setpoint + LowerThreshold + LowerOffset - Load
        else Load - Setpoint > UpperThreshold + UpperOffset - LowerThreshold
        CS->>CS: Setpoint_new = Setpoint + UpperThreshold + UpperOffset - Load
        else Load - Setpoint is between limits
        CS->>CS: Setpoint_new = 0
        end
        CS->>CS: Adjust power to setpoint
        EV->>CS: AC/DC_ChargeLoopReq()
        Note over CS: Continuous charge loop
        CS-->>EV: AC/DC_ChargeLoopRes( Setpoint_new )
        end
        else CHAdeMO
        EV->>CS: evChargingParameters
        CS->>EV: evseChargingParameters
        EV->>CS: SoC
        CSMS->>CS: SetChargingProfileRequest( v2xSchedule )
        CS-->>CSMS: SetChargingProfileResponse( Accepted )
        loop Updating setpoint dynamically every schedule period
        CS->>CS: Get power reading from grid connection
        alt Load - Setpoint < LowerThreshold + LowerOffset - UpperThreshold
        CS->>CS: Setpoint_new = Setpoint + LowerThreshold + LowerOffset - Load
        else Load - Setpoint > UpperThreshold + UpperOffset - LowerThreshold
        CS->>CS: Setpoint_new = Setpoint + UpperThreshold + UpperOffset - Load
        else Load - Setpoint is between limits
        CS->>CS: Setpoint_new = 0
        end
        CS->>CS: Adjust power to setpoint
        CS->>EV: Available output current (H'108.3)
        EV->>CS: Charging current request (H'102.3)
        end
        end
        `

        4. V2X Operation Mode LocalLoadBalancing

    2.24. Page 534 - (2026-02) - Use case Q09 has improved requirements
        (Part 2 errata - applies to this test via use case Q09)
        Changed requirements

        |  | ID. | Precondition | Requirements | Note |
        | Old | Q09.FR.02 | When Charging Station receives a [setchargingprofilerequest] with a
          [cmn_chargingscheduleperiodtype] with operationMode = LocalLoadBalancing AND / ( ( UpperThreshold or
          LowerThreshold are not set ) OR / ( UpperOffset or LowerOffset are not set ) OR / ( UpperThreshold
          is not greater than LowerThreshold ) ) | Charging Station SHALL respond with
          [setchargingprofileresponse] with status = Rejected and statusInfo = "MissingDevModelInfo" |  |
        | New | Q09.FR.02 | When Charging Station receives a [setchargingprofilerequest] with a
          [cmn_chargingscheduleperiodtype] with operationMode = LocalLoadBalancing AND / AutoThresholds =
          false or not set AND / ( ( UpperThreshold or LowerThreshold are not set ) OR / ( UpperOffset or
          LowerOffset are not set ) OR / ( UpperThreshold is not greater than LowerThreshold ) ) | Charging
          Station SHALL respond with [setchargingprofileresponse] with status = Rejected and statusInfo =
          "MissingDevModelInfo" |  |
        | Old | 09.FR.04 | Q09.FR.03 | Charging Station SHALL calculate the power setpoint as follows: / If
          Load > UpperThreshold /     DeltaSetpoint = /         UpperThreshold /         + UpperOffset - Load
          / Else If Load < / LowerThreshold /     DeltaSetpoint = /         LowerThreshold /         +
          LowerOffset - Load / Else /     DeltaSetpoint = 0 / setpoint = setpoint /         + DeltaSetpoint |
          "Load" is power from upstream meter. Positive values for consumption of energy. |
        | New | Q09.FR.04 | Q09.FR.03 | Charging Station SHALL calculate the power setpoint for EV such that
          the power reported by the upstream grid meter in steady state is reduced to a value between
          UpperThreshold + UpperOffset and LowerThreshold + LowerOffset . | See section
          [introlocalloadbalancing] for an example algorithm that can be used for this. |

        New requirement

        | ID. | Precondition | Requirements | Note |
        | Q09.FR.06 | If AutoThresholds = true | Charging Station SHALL set / * UpperThreshold =
          minChargePower, / * LowerThreshold = -minDischargePower, / * UpperOffset = -UpperThreshold, / *
          LowerOffset = -LowerThreshold / where minChargePower and minDischargePower are values from
          [notifyevchargingneedsrequest] | This will automatically regulate grid power down to 0 W while
          taking into account the minimum charging/discharging rates of the EV. |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from reusable_states.iso15118_20_transaction_just_started import V2X_VARIABLES
from smart_charging import POWER_FIELDS, request_charging_profile, v2x_profile, validate_periods
from trigger import set_variables
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# The local load-balancing settings: (instance of V2XLocalLoadBalancing, value). The values
# are the ones of the tool validation, which has 2000 for the UpperThreshold where the Manual
# Action has 1000.
THRESHOLDS = [('UpperThreshold', '2000'), ('LowerThreshold', '-1000'), ('UpperOffset', '200'),
              ('LowerOffset', '0')]


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_q_124(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # Configuration State: CS reports V2XChargingCtrlr.SupportedOperationModes that contains
    # LocalLoadBalancing
    cp.variables = dict(V2X_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Manual Action: trigger CSMS to set local load-balancing thresholds:
    #     - UpperThreshold = 1000, LowerThreshold = -1000
    #     - UpperOffset = 200, LowerOffset = 0
    # 1. The CSMS sends a SetVariablesRequest
    #    Note: CSMS may send these variables in one or multiple requests
    # 2. The Test System responds with a SetVariablesResponse with for each variable
    #    component.name V2XChargingCtrlr, component.evse.id 1, variable.name
    #    V2XLocalLoadBalancing, variable.instance <the setting> and attributeStatus Accepted
    before = len(cp.requests_of('SetVariables'))
    await set_variables(BASIC_AUTH_CP, [{
        'component': {'name': 'V2XChargingCtrlr', 'evse': {'id': 1}},
        'variable': {'name': 'V2XLocalLoadBalancing', 'instance': instance},
        'attributeValue': value,
    } for instance, value in THRESHOLDS])
    received = [item for request in cp.requests_of('SetVariables')[before:]
                for item in request.set_variable_data]
    assert len(received) == len(THRESHOLDS), \
        f"Expected {len(THRESHOLDS)} variables in the SetVariablesRequest(s), got {len(received)}"
    for index, (instance, value) in enumerate(THRESHOLDS):
        item, where = received[index], f"setVariableData[{index}]"
        assert item.component.name == 'V2XChargingCtrlr', \
            f"Expected {where}.component.name V2XChargingCtrlr, got {item.component.name}"
        assert item.component.evse is not None and item.component.evse.id == 1, \
            f"Expected {where}.component.evse.id 1, got {item.component.evse}"
        assert item.variable.name == 'V2XLocalLoadBalancing', \
            f"Expected {where}.variable.name V2XLocalLoadBalancing, got {item.variable.name}"
        assert item.variable.instance == instance, \
            f"Expected {where}.variable.instance {instance}, got {item.variable.instance}"
        assert item.attribute_value == value, \
            f"Expected {where}.attributeValue {value}, got {item.attribute_value}"

    # CSMS sets a Charging Profile with LocalLoadBalancing
    # Manual Action: trigger CSMS to set a TxDefaultProfile Charging Profile with
    #                chargingSchedulePeriod with operationMode LocalLoadBalancing
    # 3. The CSMS the sends a SetChargingProfileRequest
    # 4. The Test System responds with a SetChargingProfileResponse with
    #    - status Accepted
    request = await request_charging_profile(cp, CONFIGURED_EVSE_ID, v2x_profile(
        'TxDefaultProfile', 'Absolute', {'operationMode': 'LocalLoadBalancing'}))
    assert request.evse_id == CONFIGURED_EVSE_ID, \
        f"Expected SetChargingProfileRequest.evseId {CONFIGURED_EVSE_ID}, got {request.evse_id}"
    # operationMode must be LocalLoadBalancing; the limits, discharge limits, setpoints and
    # reactive setpoints (also those of L2 and L3) must be <omitted>
    validate_periods(request, operation_mode='LocalLoadBalancing', omitted=POWER_FIELDS)

    start_task.cancel()
