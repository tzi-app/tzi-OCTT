"""Variable monitoring of the mock Charging Station, for the diagnostics tests of OCPP 2.1
(block N): the monitors that it reports, and the requests about them that the test cases ask
the CSMS for."""

from trigger import get_variables, send_call

# MonitoringCtrlr.ItemsPerMessage[ClearVariableMonitoring] of the Test System
ITEMS_PER_MESSAGE_CLEAR_VARIABLE_MONITORING = 3

# Prerequisite: CS has implemented device model monitoring and MonitoringCtrlr.Enabled = true.
# For the station's answer to a GetVariablesRequest (TziChargePoint21.variables).
MONITORING_VARIABLES = {
    'MonitoringCtrlr.Available': 'true',
    'MonitoringCtrlr.Enabled': 'true',
    'MonitoringCtrlr.ItemsPerMessage[ClearVariableMonitoring]':
        str(ITEMS_PER_MESSAGE_CLEAR_VARIABLE_MONITORING),
}


def component_variable(component, variable, evse_id=None):
    """A ComponentVariableType, as it goes on the wire."""
    component = {'name': component}
    if evse_id is not None:
        component['evse'] = {'id': evse_id}
    return {'component': component, 'variable': {'name': variable}}


async def csms_requests_items_per_message(cp):
    """Memory State: CSMS requests ClearVariableMonitoring ItemsPerMessage from CS."""
    return await cp.wait_for_request('GetVariables', manual_action=get_variables(cp.id, [{
        'component': {'name': 'MonitoringCtrlr'},
        'variable': {'name': 'ItemsPerMessage', 'instance': 'ClearVariableMonitoring'},
    }]))


async def request_monitoring_report(cp, status, monitoring_criteria=None, component_variables=None,
                                    request_id=1):
    """The Manual Action that makes the CSMS send a GetMonitoringReportRequest for monitoring
    criteria and/or component variables, which the Test System answers with `status`.
    Returns the GetMonitoringReportRequest of the CSMS."""
    payload = {'requestId': request_id}
    if monitoring_criteria is not None:
        payload['monitoringCriteria'] = list(monitoring_criteria)
    if component_variables is not None:
        payload['componentVariable'] = list(component_variables)
    cp.set_response('GetMonitoringReport', status=status)
    return await cp.wait_for_request(
        'GetMonitoringReport', manual_action=send_call(cp.id, 'GetMonitoringReport', payload))


def validate_monitoring_criteria(request, *criteria):
    """monitoringCriteria = <criteria>, or without criteria: monitoringCriteria is omitted."""
    if criteria:
        assert request.monitoring_criteria == list(criteria), \
            f"Expected GetMonitoringReportRequest.monitoringCriteria {list(criteria)}, " \
            f"got {request.monitoring_criteria}"
    else:
        assert request.monitoring_criteria is None, \
            f"GetMonitoringReportRequest.monitoringCriteria must be omitted, " \
            f"got {request.monitoring_criteria}"


def validate_component_variable(request, index, component, variable, evse_id=None):
    """componentVariable[index] is the variable of the component (of the EVSE, when given);
    component.instance and variable.instance are omitted."""
    items = request.component_variable
    assert items is not None and len(items) > index, \
        f"GetMonitoringReportRequest has no componentVariable[{index}]: {items}"
    where = f"GetMonitoringReportRequest.componentVariable[{index}]"
    item = items[index]
    assert item.component.name == component, \
        f"Expected {where}.component.name {component}, got {item.component.name}"
    assert item.component.instance is None, \
        f"{where}.component.instance must be omitted, got {item.component.instance}"
    if evse_id is not None:
        assert item.component.evse is not None and item.component.evse.id == evse_id, \
            f"Expected {where}.component.evse.id {evse_id}, got {item.component.evse}"
    assert item.variable is not None and item.variable.name == variable, \
        f"Expected {where}.variable.name {variable}, got {item.variable}"
    assert item.variable.instance is None, \
        f"{where}.variable.instance must be omitted, got {item.variable.instance}"


def variable_monitoring(monitor_id, monitor_type, value, severity=8, transaction=False,
                        event_notification_type='CustomMonitor'):
    """A VariableMonitoringType of the Test System (snake_case)."""
    return {
        'id': monitor_id,
        'transaction': transaction,
        'value': value,
        'type': monitor_type,
        'severity': severity,
        'event_notification_type': event_notification_type,
    }


def monitoring_data(component, variable, monitors, evse_id=None):
    """A MonitoringDataType of the Test System, for a NotifyMonitoringReportRequest
    (snake_case)."""
    component = {'name': component}
    if evse_id is not None:
        component['evse'] = {'id': evse_id}
    return {'component': component, 'variable': {'name': variable},
            'variable_monitoring': list(monitors)}


# The monitors that the Test System reports
DELTA_MONITORS = [
    monitoring_data('ChargingStation', 'AvailabilityState', [variable_monitoring(1, 'Delta', 1)]),
    monitoring_data('EVSE', 'AvailabilityState', [variable_monitoring(2, 'Delta', 1)], evse_id=1),
]
THRESHOLD_MONITORS = [
    monitoring_data('ChargingStation', 'Power', [
        variable_monitoring(3, 'UpperThreshold', 22000, severity=4),
        variable_monitoring(4, 'LowerThreshold', 0, severity=6),
    ]),
]
