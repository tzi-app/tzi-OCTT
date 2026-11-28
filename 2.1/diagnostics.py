"""Log files of the mock Charging Station, for the diagnostics tests of OCPP 2.1 (use case
N01): the request for a log, and the upload of a log file over HTTP(S)."""

import asyncio
import base64
import os
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit

from trigger import send_call
from utils import build_default_ssl_context

# Where the test cases ask the Test System to upload a log, when the scenario has no upload
LOG_LOCATION = os.environ['CONFIGURED_LOG_LOCATION']

_LOG_FILE = b'2026-01-01T00:00:00Z TZI OCTT mock Charging Station: diagnostics log\n' * 8


async def request_log(cp, log_type, status='Accepted', request_id=1):
    """The Manual Action that makes the CSMS send a GetLogRequest for a log of `log_type`,
    which the Test System answers with `status`. Returns the GetLogRequest of the CSMS."""
    cp.set_response('GetLog', status=status)
    return await cp.wait_for_request(
        'GetLog',
        manual_action=send_call(cp.id, 'GetLog', {
            'logType': log_type,
            'requestId': request_id,
            'log': {'remoteLocation': LOG_LOCATION},
        }))


def validate_upload_location(location, scheme):
    """log.remoteLocation must contain a valid URL, specify the scheme, contain userinfo for
    HTTP Basic Authentication, not contain a URL fragment component, and not contain a URL
    query component that ends in a slash character ("/")."""
    try:
        url = urlsplit(location)
        url.port  # raises ValueError when the port is not a number
        valid = bool(url.scheme and url.hostname)
    except ValueError:
        valid = False
    assert valid, f"GetLogRequest.log.remoteLocation is not a valid URL: {location}"
    assert url.scheme.lower() == scheme, \
        f"Expected GetLogRequest.log.remoteLocation with scheme {scheme.upper()}, got {location}"
    assert url.username, \
        f"GetLogRequest.log.remoteLocation has no userinfo for HTTP Basic Authentication: {location}"
    assert not url.fragment and '#' not in location, \
        f"GetLogRequest.log.remoteLocation must not contain a URL fragment: {location}"
    assert not url.query.endswith('/'), \
        f"GetLogRequest.log.remoteLocation has a query component that ends in '/': {location}"


async def upload_log(location, with_userinfo=True):
    """Upload the log file of the Test System to a location using HTTP POST. Returns the HTTP
    status code of the answer.

    with_userinfo: use the userinfo of the location for HTTP Basic Authentication. False: the
    location without its userinfo.
    """
    url = urlsplit(location)
    host = url.hostname if url.port is None else f"{url.hostname}:{url.port}"
    request = urllib.request.Request(
        urlunsplit((url.scheme, host, url.path, url.query, '')), data=_LOG_FILE,
        headers={'Content-Type': 'text/plain'}, method='POST')
    if with_userinfo and url.username:
        credentials = f"{url.username}:{url.password or ''}".encode()
        request.add_header('Authorization', 'Basic ' + base64.b64encode(credentials).decode())
    context = build_default_ssl_context() if url.scheme.lower() == 'https' else None

    def post():
        try:
            with urllib.request.urlopen(request, timeout=10, context=context) as response:
                return response.status
        except urllib.error.HTTPError as error:
            return error.code

    return await asyncio.to_thread(post)


# ─── Customer information (N09, N10) ─────────────────────────────────────────

async def request_customer_information(cp, report, clear, status='Accepted', request_id=1,
                                       id_token=None, customer_identifier=None,
                                       customer_certificate=None):
    """The Manual Action that makes the CSMS send a CustomerInformationRequest about a customer
    (an idToken, a customer identifier or the hash data of a certificate, as on the wire),
    which the Test System answers with `status`. Returns the request of the CSMS."""
    payload = {'requestId': request_id, 'report': report, 'clear': clear}
    if id_token is not None:
        payload['idToken'] = id_token
    if customer_identifier is not None:
        payload['customerIdentifier'] = customer_identifier
    if customer_certificate is not None:
        payload['customerCertificate'] = customer_certificate
    cp.set_response('CustomerInformation', status=status)
    return await cp.wait_for_request(
        'CustomerInformation',
        manual_action=send_call(cp.id, 'CustomerInformation', payload))


def validate_customer_information(request, report, clear=None, id_token=None):
    """The tool validations of a CustomerInformationRequest: report, clear (when given) and
    the idToken (when given: {'idToken': ..., 'type': ...})."""
    assert request.report is report, \
        f"Expected CustomerInformationRequest.report {str(report).lower()}, got {request.report}"
    if clear is not None:
        assert request.clear is clear, \
            f"Expected CustomerInformationRequest.clear {str(clear).lower()}, got {request.clear}"
    if id_token is not None:
        assert request.id_token is not None, "CustomerInformationRequest has no idToken"
        assert request.id_token.id_token == id_token['idToken'], \
            f"Expected CustomerInformationRequest.idToken.idToken {id_token['idToken']}, " \
            f"got {request.id_token.id_token}"
        assert request.id_token.type == id_token['type'], \
            f"Expected CustomerInformationRequest.idToken.type {id_token['type']}, " \
            f"got {request.id_token.type}"
