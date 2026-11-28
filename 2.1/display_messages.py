"""Display messages for the tests of OCPP 2.1 block O: the message that the test cases ask the
CSMS to set, and the requests about it."""

import os

from trigger import send_call

# The configured values of the test cases
MESSAGE_ID = int(os.environ['CONFIGURED_DISPLAY_MESSAGE_ID'])
PRIORITY = os.environ['CONFIGURED_DISPLAY_MESSAGE_PRIORITY']
FORMAT = os.environ['CONFIGURED_DISPLAY_MESSAGE_FORMAT']
STATE = os.environ['CONFIGURED_DISPLAY_MESSAGE_STATE']
LANGUAGE = os.environ['CONFIGURED_DISPLAY_MESSAGE_LANGUAGE']
OTHER_LANGUAGE = os.environ['CONFIGURED_DISPLAY_MESSAGE_OTHER_LANGUAGE']


def display_message(message_id=MESSAGE_ID, language=None, **fields):
    """A MessageInfoType as it goes on the wire, with the configured priority and format.
    fields: other fields, such as state, startDateTime, endDateTime or transactionId."""
    content = {'format': FORMAT, 'content': 'TZI OCTT display message'}
    if language is not None:
        content['language'] = language
    message = {'id': message_id, 'priority': PRIORITY, 'message': content}
    message.update(fields)
    return message


async def request_display_message(cp, message, status='Accepted'):
    """The Manual Action that makes the CSMS send a SetDisplayMessageRequest with this
    message, which the Test System answers with `status`. Returns the request of the CSMS."""
    cp.set_response('SetDisplayMessage', status=status)
    return await cp.wait_for_request(
        'SetDisplayMessage',
        manual_action=send_call(cp.id, 'SetDisplayMessage', {'message': message}))


async def display_message_configured(cp, **fields):
    """Memory State: A display message is configured. Returns the message as the CSMS sent it
    (a Payload), which is what the Test System reports in a NotifyDisplayMessagesRequest."""
    request = await request_display_message(cp, display_message(**fields))
    return request.message


async def request_display_messages(cp, status='Accepted', request_id=1, **criteria):
    """The Manual Action that makes the CSMS send a GetDisplayMessagesRequest, which the Test
    System answers with `status`. criteria: id (a list), priority, state. Returns the
    GetDisplayMessagesRequest of the CSMS."""
    cp.set_response('GetDisplayMessages', status=status)
    return await cp.wait_for_request(
        'GetDisplayMessages',
        manual_action=send_call(cp.id, 'GetDisplayMessages', {'requestId': request_id, **criteria}))


def validate_get_display_messages(request, message_id=None, priority=None, state=None):
    """The tool validations of a GetDisplayMessagesRequest: id, priority and state must each
    have the given value, and must be omitted when that is None. requestId is there."""
    assert request.request_id is not None, "GetDisplayMessagesRequest has no requestId"
    fields = [
        ('id', request.id, None if message_id is None else [message_id]),
        ('priority', request.priority, priority),
        ('state', request.state, state),
    ]
    for name, value, expected in fields:
        if expected is None:
            assert value is None, f"GetDisplayMessagesRequest.{name} must be omitted, got {value}"
        else:
            assert value == expected, f"Expected GetDisplayMessagesRequest.{name} {expected}, got {value}"


def validate_message(request, message_id=None, priority=PRIORITY, state=None, format=None):
    """The validations of the message of a SetDisplayMessageRequest that the test cases have
    in common. A value None is not validated."""
    message = request.message
    assert message.id is not None, "SetDisplayMessageRequest.message has no id"
    if message_id is not None:
        assert message.id == message_id, \
            f"Expected SetDisplayMessageRequest.message.id {message_id}, got {message.id}"
    if priority is not None:
        assert message.priority == priority, \
            f"Expected SetDisplayMessageRequest.message.priority {priority}, got {message.priority}"
    if state is not None:
        assert message.state == state, \
            f"Expected SetDisplayMessageRequest.message.state {state}, got {message.state}"
    if format is not None:
        assert message.message.format == format, \
            f"Expected SetDisplayMessageRequest.message.message.format {format}, " \
            f"got {message.message.format}"
