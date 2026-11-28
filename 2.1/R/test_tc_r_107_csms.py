"""
Test case name      Configure DER control settings at CS
Test case Id        TC_R_107_CSMS
Use case Id(s)      R04
Requirement(s)      R04.FR.12, R04.FR.14

Requirement Details:
    R04.FR.12: CSMS SHALL not send a SetDERControlRequest that has isdefault = true for a control that has a
               startTime and/or duration field
        Note: All controls except enterService and gradient have optional startTime, duration.
    R04.FR.14: CSMS SHALL not send SetDERControlRequest that has isdefault = false for controlType =
               EnterService or Gradients
        Note: These only exist as default controls.
System under test   CSMS

Description         Setting some DER controls and reboot the charging station. After reboot, retrieving the
                    configured DER controls.

Purpose             To check if the CSMS is able to set DER Controls.

Prerequisite(s)     CSMS supports DER Control
                    The Test System must report support for the following;
                    component.name ACDERCtrlr
                    variable.name ModesSupported
                    variableAttribute.value [FreqWatt, FreqDroop, LimitMaxDischarge, Gradients, EnterService]

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
Test ClearDERControl

Manual Action: trigger CSMS to send a ClearDERControlRequest with isDefault true

1. The CSMS sends a ClearDERControlRequest
2. The Test System responds with a ClearDERControlResponse with status Accepted

Manual Action: trigger CSMS to send a ClearDERControlRequest with isDefault false

3. The CSMS sends a ClearDERControlRequest
4. The Test System responds with a ClearDERControlResponse with status Accepted

Test SetDERControl

Manual Action: trigger CSMS to send a SetDERControlRequest with isDefault true, controlType FreqDroop with
               priority 6

5. The CSMS sends a SetDERControlRequest
6. The Test System responds with a SetDERControlResponse with status Accepted

Manual Action: trigger CSMS to send a SetDERControlRequest with isDefault false controlType FreqWatt with a
               startTime, duration of 900 and priority 4

7. The CSMS sends a SetDERControlRequest
8. The Test System responds with a SetDERControlResponse with status Accepted

Manual Action: trigger CSMS to send a SetDERControlRequest for controlType EnterService with priority = 1

9. The CSMS sends a SetDERControlRequest
10. The Test System responds with a SetDERControlResponse with status Accepted

Test GetDERControl

Manual Action: trigger CSMS to send a GetDERControlRequest with isDefault true

11. The CSMS sends a GetDERControlRequest
12. The Test System responds with a GetDERControlResponse with status Accepted
13. The Test System sends a ReportDERControlRequest with
    - enterService :
    - enterService.id = "enterservice_1"
    - enterService.*enterService.highVoltage = 250
    - enterService.*enterService.lowVoltage = 210
    - enterService.*enterService.highFreq = 50.5
    - enterService.*enterService.lowFreq 49.5
    - enterService.*enterService.priority = 1

    - freqDroop :
    - freqDroop.id = "freqdroop_1"
    - freqDroop.isDefault = true
    - freqDroop.isSuperseded = false
    - freqDroop.freqDroop.priority must be 6
    - freqDroop.freqDroop.overFreq = 50.5
    - freqDroop.freqDroop.underFreq = 49.5
    - freqDroop.freqDroop.overDroop = 0.05
    - freqDroop.freqDroop.underDroop = 0.05
    - freqDroop.freqDroop.responseTime = 10
14. The CSMS sends a ReportDERControlResponse

Manual Action: trigger CSMS to send a GetDERControlRequest with isDefault false

15. The CSMS sends a GetDERControlRequest
16. The Test System responds with a GetDERControlResponse with status Accepted
17. The Test System sends a ReportDERControlRequest with
    - curve :
    - curve.id = "freqwatt_1"
    - curve.curveType = "FreqWatt"
    - curve.isDefault = false
    - curve.isSuperseded = false
    - curve.curve.priority = 4
    - curve.curve.yUnit = "PctMaxW"
    - curve.curve.curvedata[0].x = 49
    - curve.curve.curvedata[0].y = 75
    - curve.curve.curvedata[1].x = 49.5
    - curve.curve.curvedata[1].y = 90
    - curve.curve.curvedata[2].x = 50.5
    - curve.curve.curvedata[2].y = 100
    - curve.curve.curvedata[3].x = 51
    - curve.curve.curvedata[3].y = 100
    - curve.curve.startTime = <current time>
    - curve.curve.duration = 900
18. The CSMS sends a ReportDERControlResponse

Manual Action: trigger CSMS to send a GetDERControlRequest with controlType LimitMaxDischarge

19. The CSMS sends a GetDERControlRequest
20. The Test System responds with a GetDERControlResponse with status Accepted

Manual Action: trigger CSMS to send a GetDERControlRequest with a controlId

21. The CSMS sends a GetDERControlRequest
22. The Test System responds with a GetDERControlResponse with status Accepted
23. The Test System sends a NotifyDERStartStopRequest with
    - controlId <SetDERControlRequest.controlId of step 11>
    - started true
    - timestamp <Current date/time>
    - supersededIds [<SetDERControlRequest.controlId of step 9>]
24. The CSMS responds with a NotifyDERStartStopResponse

Tool validations
* Step 1:
    Message: ClearDERControlRequest
    - isDefault true
* Step 3:
    Message: ClearDERControlRequest
    - isDefault false
* Step 5:
    Message: SetDERControlRequest
    - isDefault must be true
    - controlType must be FreqDroop
    - freqDroop.priority must be 6
    - freqDroop.startTime must be <omitted>
    - freqDroop.duration must be <omitted>
    - Other optional fields must be omitted
* Step 7:
    Message: SetDERControlRequest
    - isDefault must be false
    - controlType must be FreqWatt
    - curve.priority must be 4
    - curve.startTime must be <not omitted>
    - curve.duration must be 900
    - curve.curveData[*].x must be <not omitted>
    - curve.curveData[*].y must be <not omitted>
    - Other optional fields must be omitted
* Step 9:
    Message: SetDERControlRequest
    - isDefault must be false
    - controlType must be EnterService
    - enterService must be <not omitted>
    - enterService.priority must be 1
    - Other optional fields must be omitted
* Step 11:
    Message: GetDERControlRequest
    - isDefault must be true
* Step 15:
    Message: GetDERControlRequest
    - isDefault must be false
* Step 19:
    Message: GetDERControlRequest
    - controlType must be VoltVar
* Step 21:
    Message: GetDERControlRequest
    - controlId must be <not omitted>

Post scenario validations:
    N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.26. Page 559 - (2026-09) - R04.FR.01 only applies to DC stations [1325]
        (Part 2 errata - applies to this test via use case R04)
        Use case R04 is aimed at DC charging stations for which DER controls are set in the inverter of the
        charging station. This is, however, not made specific in R04.FR.01.

        An AC charging station in principle supports every DER control, because those controls that cannot be
        executed (emulated) by the charging station will be communicated to the EV as a DER control to
        execute. If a control is sent to an EV that it cannot execute, then the EV will not be able to select
        the AC_BPT_DER service (AC_DER_IEC) in the first place, or a service renegotiation will be triggered
        to select another service during the charge parameter discovery phase (AC_DER_SAE).

        |  | ID. | Precondition | Requirements | Note |
        | Old | R04.FR.01 | Charging Station receives a [setdercontrolrequest] with a controlType that it does
          not support | Charging Station SHALL respond with [setdercontrolresponse] with status =
          NotSupported. |  |
        | New | R04.FR.01 | Charging Station receives a [setdercontrolrequest] for a DC EVSE with a
          controlType that it does not support | Charging Station SHALL respond with [setdercontrolresponse]
          with status = NotSupported. | An AC charging station in principle supports every DER control,
          because those controls that cannot be executed (emulated) by the charging station will be
          communicated to the EV as a DER control to execute. |

    6.3.21. Page 1359 - (2026-02) - TC_R_107_CSMS - Removed NotifyDERStartStopRequest and added
        ReportDERControlRequest
        | Test case name | Configure DER control settings at CS |
        | Test case Id | TC_R_107_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | … | |
        | Manual action: trigger CSMS to send a GetDERControlRequest with controlType VoltVar | |

        | Main (Test scenario) | |
        | 20. The Test System responds with a GetDERControlResponse with / status NotFound | 19. The CSMS
          sends a GetDERControlRequest |
        | Manual action: trigger CSMS to send a GetDERControlRequest with controlId from step 7 | |
        | 22. The Test System responds with a GetDERControlResponse with / status Accepted | 21. The CSMS
          sends a GetDERControlRequest |
        | [removed: 23. The Test System sends a NotifyDERStartStopRequest with] / [removed: controlId
          <SetDERControlRequest.controlId of step 11>] / [removed: started true] / [removed: timestamp
          <Current date/time>] / [removed: supersededIds [<SetDERControlRequest.controlId of step 9>]] |
          [removed: 24. The CSMS responds with a NotifyDERStartStopResponse] |
        | 23. The Test System sends a ReportDERControlRequest with / - curve : / - curve.id = "freqwatt_1" / -
          curve.curveType = "FreqWatt" / - curve.isDefault = false / - curve.isSuperseded = false / -
          curve.curve.priority = 4 / - curve.curve.yUnit = "PctMaxW" / - curve.curve.curvedata[0].x = 49 / -
          curve.curve.curvedata[0].y = 75 / - curve.curve.curvedata[1].x = 49.5 / - curve.curve.curvedata[1].y
          = 90 / - curve.curve.curvedata[2].x = 50.5 / - curve.curve.curvedata[2].y = 100 / -
          curve.curve.curvedata[3].x = 51 / - curve.curve.curvedata[3].y = 100 / - curve.curve.startTime =
          <current time> / - curve.curve.duration = 900 | 24. The CSMS sends a ReportDERControlResponse |

        | Tool validations |
        | … / \\* Step 21: / Message: GetDERControlRequest / - controlId must be <controlId from step 7> |
        | Post scenario validations: / N/a |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']

# The DER controls of the scenario: their ids, and their settings as they go on the wire
FREQ_DROOP_ID, FREQ_WATT_ID, ENTER_SERVICE_ID = 'freqdroop_1', 'freqwatt_1', 'enterservice_1'
FREQ_DROOP = {'priority': 6, 'overFreq': 50.5, 'underFreq': 49.5, 'overDroop': 0.05,
              'underDroop': 0.05, 'responseTime': 10}
FREQ_WATT_CURVE_DATA = [{'x': 49, 'y': 75}, {'x': 49.5, 'y': 90}, {'x': 50.5, 'y': 100},
                        {'x': 51, 'y': 100}]
ENTER_SERVICE = {'priority': 1, 'highVoltage': 250, 'lowVoltage': 210, 'highFreq': 50.5,
                 'lowFreq': 49.5}


async def request_der_control(cp, action, payload, status='Accepted'):
    """The Manual Action that makes the CSMS send a ClearDERControl-, SetDERControl- or
    GetDERControlRequest, which the Test System answers with `status`."""
    cp.set_response(action, status=status)
    return await cp.wait_for_request(action, manual_action=send_call(cp.id, action, payload))


def validate_only(request, *fields):
    """Other optional fields must be omitted: the request has these fields and no others."""
    assert set(request) == set(fields), \
        f"Expected a SetDERControlRequest with only {sorted(fields)}, got {sorted(request)}"


async def report_freq_watt_curve(cp, request_id, start_time):
    """The Test System sends a ReportDERControlRequest with the FreqWatt curve "freqwatt_1"."""
    await cp.call(call.ReportDERControl(request_id=request_id, curve=[{
        'id': FREQ_WATT_ID,
        'curve_type': 'FreqWatt',
        'is_default': False,
        'is_superseded': False,
        'curve': {
            'priority': 4,
            'y_unit': 'PctMaxW',
            'curve_data': FREQ_WATT_CURVE_DATA,
            'start_time': start_time,
            'duration': 900,
        },
    }]))


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_r_107(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: CSMS supports DER Control
    # The scenario has the steps 19 to 24 of errata 2026-09 (6.3.21).

    # Test ClearDERControl
    # Manual Action: trigger CSMS to send a ClearDERControlRequest with isDefault true
    # 1. The CSMS sends a ClearDERControlRequest
    # 2. The Test System responds with a ClearDERControlResponse with status Accepted
    request = await request_der_control(cp, 'ClearDERControl', {'isDefault': True})
    assert request.is_default is True, \
        f"Expected ClearDERControlRequest.isDefault true, got {request.is_default}"

    # Manual Action: trigger CSMS to send a ClearDERControlRequest with isDefault false
    # 3. The CSMS sends a ClearDERControlRequest
    # 4. The Test System responds with a ClearDERControlResponse with status Accepted
    request = await request_der_control(cp, 'ClearDERControl', {'isDefault': False})
    assert request.is_default is False, \
        f"Expected ClearDERControlRequest.isDefault false, got {request.is_default}"

    # Test SetDERControl
    # Manual Action: trigger CSMS to send a SetDERControlRequest with isDefault true, controlType
    #                FreqDroop with priority 6
    # 5. The CSMS sends a SetDERControlRequest
    # 6. The Test System responds with a SetDERControlResponse with status Accepted
    request = await request_der_control(cp, 'SetDERControl', {
        'isDefault': True, 'controlId': FREQ_DROOP_ID, 'controlType': 'FreqDroop',
        'freqDroop': FREQ_DROOP,
    })
    assert request.is_default is True, f"Expected isDefault true, got {request.is_default}"
    assert request.control_type == 'FreqDroop', f"Expected controlType FreqDroop, got {request.control_type}"
    assert request.freq_droop is not None and request.freq_droop.priority == 6, \
        f"Expected freqDroop.priority 6, got {request.freq_droop}"
    assert request.freq_droop.start_time is None, \
        f"freqDroop.startTime must be omitted, got {request.freq_droop.start_time}"
    assert request.freq_droop.duration is None, \
        f"freqDroop.duration must be omitted, got {request.freq_droop.duration}"
    validate_only(request, 'is_default', 'control_id', 'control_type', 'freq_droop')

    # Manual Action: trigger CSMS to send a SetDERControlRequest with isDefault false controlType
    #                FreqWatt with a startTime, duration of 900 and priority 4
    # 7. The CSMS sends a SetDERControlRequest
    # 8. The Test System responds with a SetDERControlResponse with status Accepted
    start_time = utc_now_iso()
    freq_watt = await request_der_control(cp, 'SetDERControl', {
        'isDefault': False, 'controlId': FREQ_WATT_ID, 'controlType': 'FreqWatt',
        'curve': {'priority': 4, 'yUnit': 'PctMaxW', 'curveData': FREQ_WATT_CURVE_DATA,
                  'startTime': start_time, 'duration': 900},
    })
    assert freq_watt.is_default is False, f"Expected isDefault false, got {freq_watt.is_default}"
    assert freq_watt.control_type == 'FreqWatt', \
        f"Expected controlType FreqWatt, got {freq_watt.control_type}"
    curve = freq_watt.curve
    assert curve is not None and curve.priority == 4, f"Expected curve.priority 4, got {curve}"
    assert curve.start_time is not None, "curve.startTime must not be omitted"
    assert curve.duration == 900, f"Expected curve.duration 900, got {curve.duration}"
    assert all(point.x is not None and point.y is not None for point in curve.curve_data), \
        f"curve.curveData[*].x and .y must not be omitted: {curve.curve_data}"
    validate_only(freq_watt, 'is_default', 'control_id', 'control_type', 'curve')

    # Manual Action: trigger CSMS to send a SetDERControlRequest for controlType EnterService with
    #                priority = 1
    # 9. The CSMS sends a SetDERControlRequest
    # 10. The Test System responds with a SetDERControlResponse with status Accepted
    request = await request_der_control(cp, 'SetDERControl', {
        'isDefault': False, 'controlId': ENTER_SERVICE_ID, 'controlType': 'EnterService',
        'enterService': ENTER_SERVICE,
    })
    assert request.is_default is False, f"Expected isDefault false, got {request.is_default}"
    assert request.control_type == 'EnterService', \
        f"Expected controlType EnterService, got {request.control_type}"
    assert request.enter_service is not None, "enterService must not be omitted"
    assert request.enter_service.priority == 1, \
        f"Expected enterService.priority 1, got {request.enter_service.priority}"
    validate_only(request, 'is_default', 'control_id', 'control_type', 'enter_service')

    # Test GetDERControl
    # Manual Action: trigger CSMS to send a GetDERControlRequest with isDefault true
    # 11. The CSMS sends a GetDERControlRequest
    # 12. The Test System responds with a GetDERControlResponse with status Accepted
    request = await request_der_control(cp, 'GetDERControl', {'requestId': 1, 'isDefault': True})
    assert request.is_default is True, \
        f"Expected GetDERControlRequest.isDefault true, got {request.is_default}"

    # 13. The Test System sends a ReportDERControlRequest with
    #     - enterService: id "enterservice_1", highVoltage 250, lowVoltage 210, highFreq 50.5,
    #       lowFreq 49.5, priority 1
    #     - freqDroop: id "freqdroop_1", isDefault true, isSuperseded false, priority 6, overFreq
    #       50.5, underFreq 49.5, overDroop 0.05, underDroop 0.05, responseTime 10
    # 14. The CSMS sends a ReportDERControlResponse
    await cp.call(call.ReportDERControl(
        request_id=request.request_id,
        enter_service=[{'id': ENTER_SERVICE_ID, 'enter_service': ENTER_SERVICE}],
        freq_droop=[{'id': FREQ_DROOP_ID, 'is_default': True, 'is_superseded': False,
                     'freq_droop': FREQ_DROOP}],
    ))

    # Manual Action: trigger CSMS to send a GetDERControlRequest with isDefault false
    # 15. The CSMS sends a GetDERControlRequest
    # 16. The Test System responds with a GetDERControlResponse with status Accepted
    request = await request_der_control(cp, 'GetDERControl', {'requestId': 2, 'isDefault': False})
    assert request.is_default is False, \
        f"Expected GetDERControlRequest.isDefault false, got {request.is_default}"

    # 17. The Test System sends a ReportDERControlRequest with
    #     - curve: id "freqwatt_1", curveType "FreqWatt", isDefault false, isSuperseded false,
    #       priority 4, yUnit "PctMaxW", curveData (49, 75), (49.5, 90), (50.5, 100), (51, 100),
    #       startTime <current time>, duration 900
    # 18. The CSMS sends a ReportDERControlResponse
    await report_freq_watt_curve(cp, request.request_id, start_time)

    # Manual action: trigger CSMS to send a GetDERControlRequest with controlType VoltVar
    # 19. The CSMS sends a GetDERControlRequest
    # 20. The Test System responds with a GetDERControlResponse with status NotFound
    request = await request_der_control(
        cp, 'GetDERControl', {'requestId': 3, 'controlType': 'VoltVar'}, status='NotFound')
    assert request.control_type == 'VoltVar', \
        f"Expected GetDERControlRequest.controlType VoltVar, got {request.control_type}"

    # Manual action: trigger CSMS to send a GetDERControlRequest with controlId from step 7
    # 21. The CSMS sends a GetDERControlRequest
    # 22. The Test System responds with a GetDERControlResponse with status Accepted
    request = await request_der_control(
        cp, 'GetDERControl', {'requestId': 4, 'controlId': freq_watt.control_id})
    assert request.control_id == freq_watt.control_id, \
        f"Expected GetDERControlRequest.controlId {freq_watt.control_id} (the one of step 7), " \
        f"got {request.control_id}"

    # 23. The Test System sends a ReportDERControlRequest with the curve "freqwatt_1", as in
    #     step 17
    # 24. The CSMS sends a ReportDERControlResponse
    await report_freq_watt_curve(cp, request.request_id, start_time)

    start_task.cancel()
