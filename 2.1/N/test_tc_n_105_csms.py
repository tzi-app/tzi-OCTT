"""
Test case name      Set Variable Monitoring - Set Frequent Periodic Variable Monitoring - Periodic
Test case Id        TC_N_105_CSMS
Use case Id(s)      N11, N14, N15
Requirement(s)      N11.FR.06, N11.FR.08, N14.FR.01, N15.FR.02

Requirement Details:
    N11.FR.06: CSMS SHALL respond with a OpenPeriodicEventStreamResponse with status = Accepted.
        Precondition: When CSMS accepts the periodic event stream
    N11.FR.08: CSMS SHALL associate the following data, that is normally present as required fields in a
               NotifyEventRequest, with the periodic event stream. (This data is available from the monitor):
               • variableMonitoringId,
               • trigger (= Periodic),
               • eventNotificationType,
               • severity,
               • component,
               • variable.
    N14.FR.01: CSMS SHALL send a AdjustPeriodicEventStreamRequest message with the id of the event stream and
               a params object with new interval and/or values fields
        Precondition: When CSMS wants to change the rate of sending data for a periodic event stream
    N15.FR.02: CSMS SHALL NOT confirm the message upon receipt with "CALLRESULT" or "CALLERROR".
        Precondition: When receiving a message of RPC message type "SEND"
System under test   CSMS

Description         To give the CSMS the ability to request efficient frequent periodic monitoring of
                    variables.

Purpose             To verify if the CSMS can accept and receive periodic event streams.

Prerequisite(s)     - The CSMS supports periodic event streams.

Configuration State CSMS must be configured to accept opening the periodic event stream.

Memory State        N/a

Reusable State      N/a

Test Scenario
1. Test System sends a OpenPeriodicEventStreamRequest with
    - constantStreamData.id 2
    - constantStreamData.variableMonitoringId 3
    - constantStreamData.params.interval 10
    - constantStreamData.params.values 30
2. CSMS responds with a OpenPeriodicEventStreamResponse

Manual Action: Request the CSMS to reconfigure the periodic event stream to an interval of 15s and values 45

3. CSMS sends a AdjustPeriodicEventStreamRequest
4. Test System responds with a AdjustPeriodicEventStreamResponse with
    - status Accepted
5. Charging Station sends a NotifyPeriodicEventStream using RFC framework SEND
6. Test System sends a ClosePeriodicEventStreamRequest with
    - constantStreamData.id 2
7. CSMS responds with a OpenPeriodicEventStreamResponse

Note: The Test System waits 10 seconds, before ending the testcase.

Tool validations
* Step 2:
    Message OpenPeriodicEventStreamResponse
    - status must be Accepted
* Step 3:
    Message AdjustPeriodicEventStreamRequest
    - id must be 2
    - params.interval must be 15
    - params.values must be 45

Post scenario validations:
    - CSMS does not respond with any message when receiving message NotifyPeriodicEventStream of step 5.

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.19. Page 1309 - (2026-02) - TC_N_105_CSMS - Install usable monitor and send a
        NotifyPeriodicEventStream
        | Test case name | Set Variable Monitoring - Set Frequent Periodic Variable Monitoring - Periodic |
        | Test case Id | TC_N_105_CSMS |
        | … | |

        | Before (Preparations) |
        | Configuration State: / [removed: CSMS must be configured to accept opening the periodic event
          stream.] / N/a |
        | Memory State: / N/a |
        | Reusable State: / N/a |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | Manual Action : Request CSMS to install a monitor on: / component.name EVSE / EVSE.id <Configured
          evseId> / variable.name Power / type Periodic / severity 8 / value 5 / periodicEventStream.interval
          5 / periodicEventStream.values 10 | |
        | 2. Test System responds with: / Message: SetVariableMonitoringResponse with /
          setMonitoringResult[0].status = Accepted | 1. CSMS sends a SetVariableMonitoringRequest |

        | Main (Test scenario) | |
        | [removed: 1.] 3. Test System sends a OpenPeriodicEventStreamRequest with / constantStreamData.id 2 /
          constantStreamData.variableMonitoringId [removed: 3] <monitor id from step 1> /
          constantStreamData.params.interval [removed: 10] 5 / constantStreamData.params.values [removed: 30]
          10 | [removed: 2.] 4. CSMS responds with a OpenPeriodicEventStreamResponse |
        | Note : The Test System waits 5 seconds. | |
        | 5. Test System sends a NotifyPeriodicEventStream using RFC framework SEND | |
        | Manual Action: Request the CSMS to reconfigure the periodic event stream to an interval of 15s and
          values 45 | |
        | [removed: 4.] 7. Test System responds with a AdjustPeriodicEventStreamResponse with / status
          Accepted | [removed: 3.] 6. CSMS sends a AdjustPeriodicEventStreamRequest |
        | Note : The Test System waits 10 seconds. | |
        | [removed: 5.] 8. Test System sends a NotifyPeriodicEventStream using RFC framework SEND | |
        | [removed: 6.] 9. Test System sends a ClosePeriodicEventStreamRequest with / constantStreamData.id 2
          | [removed: 7.] 10. CSMS responds with a ClosePeriodicEventStreamResponse |
        | Note: [removed: The Test System waits 10 seconds, before ending the testcase.] | |

        | Tool validations |
        | \\* Step 1: / Message SetVariableMonitoringRequest with: / - setMonitoringData[0].type = Periodic, /
          - setMonitoringData[0].severity = 8, / - setMonitoringData[0].component.name = "EVSE" / -
          setMonitoringData[0].component.evse.id = <Configured evseId> / - setMonitoringData[0].variable.name
          = Power / - setMonitoringData[0].value = 5 / - setMonitoringData[0].periodicEventStream.interval 5 /
          - setMonitoringData[0].periodicEventStream.values 10 / \\* [removed: Step 2:] Step 4: / Message
          OpenPeriodicEventStreamResponse / - status must be Accepted / \\* [removed: Step 3:] Step 6: /
          Message AdjustPeriodicEventStreamRequest / id must be 2 / params.interval must be [removed: 15] 10 /
          params.values must be [removed: 45] 20 |
"""

import asyncio
import os

import pytest
from ocpp.v21 import call

from charge_point import TziChargePoint21
from monitoring import MONITORING_VARIABLES
from ocpp_messages import utc_now_iso
from reusable_states.booted import booted
from trigger import send_call
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])

# The id that the Test System gives the monitor of step 1, and the id of its event stream
MONITOR_ID = 3
STREAM_ID = 2


async def send_periodic_event_stream(cp, interval, values):
    """The Test System sends a NotifyPeriodicEventStream using RPC framework SEND, with the
    values of the monitored variable of the last interval. The CSMS does not respond with any
    message when it receives it."""
    unique_id = await cp.send_unconfirmed('NotifyPeriodicEventStream', {
        'id': STREAM_ID,
        'pending': 0,
        'basetime': utc_now_iso(-interval),
        'data': [{'t': float(second), 'v': str(1000.0 + second)} for second in range(values)],
    })
    await asyncio.sleep(1)
    responses = [message for message in cp.unexpected_responses if message[1] == unique_id]
    assert not responses, \
        f"The CSMS responded to the NotifyPeriodicEventStream that was sent with SEND: {responses}"


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_n_105(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    # The Test System has implemented device model monitoring.
    cp.variables = dict(MONITORING_VARIABLES)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The scenario is the one of errata 2026-09 (6.3.19).

    # Manual Action: Request CSMS to install a monitor on: component.name EVSE, EVSE.id
    #                <Configured evseId>, variable.name Power, type Periodic, severity 8, value 5,
    #                periodicEventStream.interval 5, periodicEventStream.values 10
    # 1. CSMS sends a SetVariableMonitoringRequest
    # 2. Test System responds with: SetVariableMonitoringResponse with
    #    setMonitoringResult[0].status = Accepted
    cp.set_response('SetVariableMonitoring', lambda request: {'set_monitoring_result': [
        {'id': MONITOR_ID + index, 'status': 'Accepted', 'type': item.type, 'severity': item.severity,
         'component': item.component, 'variable': item.variable}
        for index, item in enumerate(request.set_monitoring_data)]})
    request = await cp.wait_for_request(
        'SetVariableMonitoring',
        manual_action=send_call(BASIC_AUTH_CP, 'SetVariableMonitoring', {'setMonitoringData': [{
            'value': 5,
            'type': 'Periodic',
            'severity': 8,
            'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}},
            'variable': {'name': 'Power'},
            'periodicEventStream': {'interval': 5, 'values': 10},
        }]}))
    monitor = request.set_monitoring_data[0]
    assert monitor.type == 'Periodic', f"Expected setMonitoringData[0].type Periodic, got {monitor.type}"
    assert monitor.severity == 8, f"Expected setMonitoringData[0].severity 8, got {monitor.severity}"
    assert monitor.component.name == 'EVSE', \
        f"Expected setMonitoringData[0].component.name EVSE, got {monitor.component.name}"
    assert monitor.component.evse is not None and monitor.component.evse.id == CONFIGURED_EVSE_ID, \
        f"Expected setMonitoringData[0].component.evse.id {CONFIGURED_EVSE_ID}, got {monitor.component.evse}"
    assert monitor.variable.name == 'Power', \
        f"Expected setMonitoringData[0].variable.name Power, got {monitor.variable.name}"
    assert monitor.value == 5, f"Expected setMonitoringData[0].value 5, got {monitor.value}"
    stream = monitor.periodic_event_stream
    assert stream is not None and stream.interval == 5 and stream.values == 10, \
        f"Expected setMonitoringData[0].periodicEventStream interval 5 and values 10, got {stream}"

    # 3. Test System sends a OpenPeriodicEventStreamRequest with
    #    - constantStreamData.id 2
    #    - constantStreamData.variableMonitoringId <monitor id from step 1>
    #    - constantStreamData.params.interval 5
    #    - constantStreamData.params.values 10
    # 4. CSMS responds with a OpenPeriodicEventStreamResponse
    response = await cp.call(call.OpenPeriodicEventStream(constant_stream_data={
        'id': STREAM_ID,
        'variable_monitoring_id': MONITOR_ID,
        'params': {'interval': 5, 'values': 10},
    }))
    assert response.status == 'Accepted', \
        f"Expected OpenPeriodicEventStreamResponse.status Accepted, got {response.status}"

    # Note: The Test System waits 5 seconds.
    # 5. Test System sends a NotifyPeriodicEventStream using RPC framework SEND
    await asyncio.sleep(5)
    await send_periodic_event_stream(cp, interval=5, values=10)

    # Manual Action: Request the CSMS to reconfigure the periodic event stream [to an interval of
    #                10 s and 20 values: the ones that the tool validation of the errata has]
    # 6. CSMS sends a AdjustPeriodicEventStreamRequest
    # 7. Test System responds with a AdjustPeriodicEventStreamResponse with
    #    - status Accepted
    cp.set_response('AdjustPeriodicEventStream', status='Accepted')
    request = await cp.wait_for_request(
        'AdjustPeriodicEventStream',
        manual_action=send_call(BASIC_AUTH_CP, 'AdjustPeriodicEventStream', {
            'id': STREAM_ID,
            'params': {'interval': 10, 'values': 20},
        }))
    assert request.id == STREAM_ID, \
        f"Expected AdjustPeriodicEventStreamRequest.id {STREAM_ID}, got {request.id}"
    assert request.params.interval == 10, \
        f"Expected AdjustPeriodicEventStreamRequest.params.interval 10, got {request.params.interval}"
    assert request.params.values == 20, \
        f"Expected AdjustPeriodicEventStreamRequest.params.values 20, got {request.params.values}"

    # Note: The Test System waits 10 seconds.
    # 8. Test System sends a NotifyPeriodicEventStream using RPC framework SEND
    await asyncio.sleep(10)
    await send_periodic_event_stream(cp, interval=10, values=20)

    # 9.  Test System sends a ClosePeriodicEventStreamRequest with
    #     - constantStreamData.id 2
    # 10. CSMS responds with a ClosePeriodicEventStreamResponse
    await cp.call(call.ClosePeriodicEventStream(id=STREAM_ID))

    start_task.cancel()
