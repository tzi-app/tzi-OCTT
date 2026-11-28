"""
Test case name      Set DisplayMessage - Language preference of the EV Driver
Test case Id        TC_O_101_CSMS
Use case Id(s)      O01
Requirement(s)      N/a
System under test   CSMS

Description         This test case describes how the CSMS can be requested to sent an SetDisplayMessageRequest
                    to the charging station. Depending on the given parameters the message shall be displayed
                    a certain way and at a certain moment on the Charging Station. These messages are
                    displayed additionally on a Charging Station and are not part of the firmware.

Purpose             To verify if the CSMS is able to send a DisplayMessage with the default and a different
                    language.

Prerequisite(s)     CSMS support multiple languages.

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
Manual Action: Request the CSMS to send a SetDisplayMessageRequest with an additional language (other than the
               default language), that is supported on the charging station.

1. The CSMS sends a SetDisplayMessageRequest
2. The Test System responds with a SetDisplayMessageResponse with status Accepted

Tool validations
* Step 1:
    Message SetDisplayMessageRequest
    - message.id <Generated Id>
    - message.priority <Configured Priority>
    - message.message.language <Not omitted default language>
    - message.message.content <Not omitted default language content>
    - message.messageExtra[0].language <Not omitted other language>
    - message.messageExtra]0].content <Not omitted other language content>

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.14. Page 1333 - (2026-02) - TC_O_101_CSMS - Updated tool validations
        | Tool validations |
        | * Step 1: / Message SetDisplayMessageRequest / - message.id <Generated Id> / - message.priority
          <Configured Priority> / - message.message.language [removed: <Not omitted default language>] <Not
          omitted> / [removed: - message.message.content <Not omitted default language content>] / -
          message.messageExtra[0].language [removed: <Not omitted other language>] <Different from
          message.language> / [removed: - message.messageExtra]0].content <Not omitted other language
          content>] |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from display_messages import (
    display_message,
    FORMAT,
    LANGUAGE,
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
async def test_tc_o_101(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # Prerequisite: CSMS support multiple languages.
    # Manual Action: Request the CSMS to send a SetDisplayMessageRequest with an additional
    #                language (other than the default language), that is supported on the
    #                charging station.
    # 1. The CSMS sends a SetDisplayMessageRequest
    # 2. The Test System responds with a SetDisplayMessageResponse with status Accepted
    request = await request_display_message(cp, display_message(language=LANGUAGE, messageExtra=[
        {'format': FORMAT, 'language': OTHER_LANGUAGE, 'content': 'TZI OCTT schermbericht'}]))
    # The tool validations of errata 2026-09 (6.3.14): message.id <Generated Id>,
    # message.priority <Configured Priority>, message.message.language <Not omitted>,
    # message.messageExtra[0].language <Different from message.language>
    validate_message(request)
    message = request.message
    assert message.message.language is not None, \
        "SetDisplayMessageRequest.message.message.language must not be omitted"
    assert message.message_extra, "SetDisplayMessageRequest.message has no messageExtra"
    assert message.message_extra[0].language is not None \
        and message.message_extra[0].language != message.message.language, \
        f"message.messageExtra[0].language must be different from message.message.language " \
        f"{message.message.language}, got {message.message_extra[0].language}"

    start_task.cancel()
