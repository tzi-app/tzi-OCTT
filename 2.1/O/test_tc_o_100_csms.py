"""
Test case name      Set Display Message - unsupported language
Test case Id        TC_O_100_CSMS
Use case Id(s)      O01
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to handle a rejection request for DisplayMessage mechanism
                    as result of an unsupported language status.

Prerequisite(s)     CSMS support multiple languages.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a SetDisplayMessageRequest with a certain language. Test System will
               respond that the language is not supported.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status LanguageNotSupported

Manual Action: Verify that CSMS UI reports that message was not accepted due to unknown language

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.id <Generated Id>
    - message.priority <Configured Priority>
    - message.message.language <Not omitted>

Post scenario validations:
    - N/a
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import (
    display_message,
    OTHER_LANGUAGE,
    request_display_message,
    validate_message,
)
from reusable_states.booted import booted
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_o_100(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: CSMS support multiple languages.
    # Manual Action: Request the CSMS to send a SetDisplayMessageRequest with a certain language.
    #                Test System will respond that the language is not supported.
    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status
    #    LanguageNotSupported
    request = await request_display_message(
        cp, display_message(language=OTHER_LANGUAGE), status='LanguageNotSupported')
    # message.id <Generated Id>, message.priority <Configured Priority>, message.message.language
    # <Not omitted>
    validate_message(request)
    assert request.message.message.language is not None, \
        "SetDisplayMessageRequest.message.message.language must not be omitted"

    # Manual Action: Verify that CSMS UI reports that message was not accepted due to unknown
    #                language. That is a check in the CSMS itself.

    start_task.cancel()
