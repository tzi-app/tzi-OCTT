"""Helpers for the device model messages (GetVariables, SetVariables, reports) in the OCPP 2.1
tests."""


def find_variable(items, component, variable, instance=None):
    """The element about <component>.<variable> (and the variable instance) in a list such as
    getVariableData, setVariableData or componentVariable, or None. The elements may be in any
    order."""
    for item in items or []:
        if (item.component.name == component
                and item.variable is not None
                and item.variable.name == variable
                and item.variable.instance == instance):
            return item
    return None


def variable_key(item):
    """(component.name, variable.name, variable.instance) of such an element."""
    return item.component.name, item.variable.name, item.variable.instance


def _report_data(component, variable, value, mutability, data_type, values_list=None):
    """A ReportDataType element."""
    characteristics = {'data_type': data_type, 'supports_monitoring': True}
    if values_list is not None:
        characteristics['values_list'] = values_list
    return {
        'component': component,
        'variable': variable,
        'variable_attribute': [{'type': 'Actual', 'value': value, 'mutability': mutability}],
        'variable_characteristics': characteristics,
    }


_AVAILABILITY_STATES = 'Available,Occupied,Reserved,Unavailable,Faulted'

# The part of the simulated station's device model that the report tests send.
# Variables that an operator can set:
CONFIGURATION_INVENTORY = [
    _report_data({'name': 'OCPPCommCtrlr'}, {'name': 'OfflineThreshold'}, '60', 'ReadWrite', 'integer'),
    _report_data({'name': 'OCPPCommCtrlr'}, {'name': 'HeartbeatInterval'}, '300', 'ReadWrite', 'integer'),
    _report_data({'name': 'AuthCtrlr'}, {'name': 'AuthorizeRemoteStart'}, 'true', 'ReadWrite', 'boolean'),
    _report_data({'name': 'TxCtrlr'}, {'name': 'EVConnectionTimeOut'}, '120', 'ReadWrite', 'integer'),
]

# Variables about the station's current charging availability and problem conditions:
SUMMARY_INVENTORY = [
    _report_data({'name': 'ChargingStation'}, {'name': 'AvailabilityState'}, 'Available',
                 'ReadOnly', 'OptionList', _AVAILABILITY_STATES),
    _report_data({'name': 'EVSE', 'evse': {'id': 1}}, {'name': 'AvailabilityState'}, 'Available',
                 'ReadOnly', 'OptionList', _AVAILABILITY_STATES),
    _report_data({'name': 'Connector', 'evse': {'id': 1, 'connector_id': 1}},
                 {'name': 'AvailabilityState'}, 'Available', 'ReadOnly', 'OptionList',
                 _AVAILABILITY_STATES),
]

# All variables:
FULL_INVENTORY = CONFIGURATION_INVENTORY + SUMMARY_INVENTORY + [
    _report_data({'name': 'DeviceDataCtrlr'}, {'name': 'ItemsPerMessage', 'instance': 'GetVariables'},
                 '4', 'ReadOnly', 'integer'),
    _report_data({'name': 'DeviceDataCtrlr'}, {'name': 'ItemsPerMessage', 'instance': 'GetReport'},
                 '4', 'ReadOnly', 'integer'),
    _report_data({'name': 'SecurityCtrlr'}, {'name': 'SecurityProfile'}, '1', 'ReadOnly', 'integer'),
]


async def send_report(cp, request_id, report_data, parts=2):
    """Send a report as the NotifyReportRequests of one requestId: `parts` messages, of which
    all but the last have tbc (to be continued) true."""
    size = max(1, -(-len(report_data) // parts))
    chunks = [report_data[start:start + size] for start in range(0, len(report_data), size)]
    for seq_no, chunk in enumerate(chunks):
        await cp.send_notify_report(
            request_id=request_id,
            seq_no=seq_no,
            report_data=chunk,
            tbc=seq_no < len(chunks) - 1,
        )
