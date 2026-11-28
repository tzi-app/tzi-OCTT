"""
State               ISO15118-20 transaction just started
System under test   CSMS
Description         Starts ISO15118-20 transaction
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      State is EVConnectedPreSession

Main

1. The Test System sends an AuthorizeRequest with
   idToken.type eMAID
   idToken.type <Configured ISO15118 idToken>
   iso15118CertificateHashData <hashData’s from MO certificate chain>
2. The CSMS responds with an AuthorizeResponse
   - allowedEnergyTransfer [<csms_allowedEnergyTransferModes>]
3. The Test System sends a TransactionEventRequest with
   eventType Started
   transactionInfo.transactionId <transactionId>
   idToken.additionalInfo.additionalIdToken <Configured EVCCID>
   idToken.additionalInfo.additionalInfo.type EVCCID
4. The CSMS responds with a TransactionEventResponse

Tool validations
* Step 2: Message: AuthorizeResponse - idTokenInfo.status must be Accepted
* Step 4: Message: TransactionEventResponse - idTokenInfo.status must be Accepted
Post condition      N/a

Remarks
Exposes <allowedEnergyTransferModes>
<transactionId>
Prerequisite(s) Test System reported support for V2XChargingCtrlr.V2XEnabled for configured EVSEs with value
true

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    6.3.23. Page 1383 - (2026-04) - Additional validation added for certificateStatus
        The certificateStatus should be included in AuthorizeResponse when certificate or
        iso15118CertificateHashData is included in the AuthorizeRequest.

        | State | ISO15118-20 transaction just started |
        | System under test | CSMS |
        | … | |

        | Tool validations |
        | * Step 2: / Message: AuthorizeResponse / - idTokenInfo.status must be Accepted / - certificateStatus
          must be Accepted / * Step 4: / Message: TransactionEventResponse / - idTokenInfo.status must be
          Accepted |
        | Post scenario validations: / N/a |
"""

import os

from ocpp.v21 import call

from authorization import validate_id_token_info
from charge_point import ChargingSession, TziChargePoint21
from contract_pki import contract_chain_hash_data
from mock_ocsp_responder import MockOCSPResponder
from ocpp_messages import utc_now_iso
from reusable_states.ev_connected_pre_session import ev_connected_pre_session

# <Configured ISO15118 idToken>: the eMAID of the configured contract certificate
EMAID_ID_TOKEN = os.environ['EMAID_ID_TOKEN']
# <Configured EVCCID>: the id of the communication controller of the mock EV
CONFIGURED_EVCCID = os.environ['CONFIGURED_EVCCID']

# The OCSP service of the Test System, which the responder URL of the hash data points to
OCSP_PORT = 19080

# What the Test System reports in its device model for these test cases. Prerequisite: Test
# System reported support for V2XChargingCtrlr.V2XEnabled for configured EVSEs with value true
V2X_VARIABLES = {
    'ISO15118Ctrlr.Enabled': 'true',
    'V2XChargingCtrlr.Enabled': 'true',
    'V2XChargingCtrlr.SupportedEnergyTransferModes':
        'AC_single_phase,AC_two_phase,AC_three_phase,AC_BPT,AC_BPT_DER,AC_DER',
    'V2XChargingCtrlr.SupportedOperationModes':
        'ChargingOnly,CentralSetpoint,CentralFrequency,LocalFrequency,ExternalSetpoint,'
        'ExternalLimits,LocalLoadBalancing,Idle',
}


async def iso15118_20_transaction_just_started(cp: TziChargePoint21,
                                               session: ChargingSession = None):
    """Returns what the state exposes: (<allowedEnergyTransferModes>, <transactionId>).
    The first is None when the CSMS left allowedEnergyTransfer out of its AuthorizeResponse.

    The Test System has to report V2X_VARIABLES (TziChargePoint21.variables).
    session: the charging session this is about, when the scenario has more than one.
    """
    session = session or cp.session

    # Before: State is EVConnectedPreSession
    # The transaction of this state starts in step 3, so the EV is connected and there is no
    # transaction yet.
    if not session.ev_connected:
        await ev_connected_pre_session(cp, session=session, starts_transaction=False)

    # 1. The Test System sends an AuthorizeRequest with
    #    idToken.type eMAID
    #    idToken.idToken <Configured ISO15118 idToken>
    #    iso15118CertificateHashData <hashData's from MO certificate chain>
    # 2. The CSMS responds with an AuthorizeResponse
    #    - allowedEnergyTransfer [<csms_allowedEnergyTransferModes>]
    ocsp_responder = MockOCSPResponder(port=OCSP_PORT, cert_status="good")
    ocsp_responder.start()
    try:
        response = await cp.send_authorization_request_with_iso15118(
            id_token=EMAID_ID_TOKEN,
            token_type='eMAID',
            iso15118_certificate_hash_data=contract_chain_hash_data(
                f"http://localhost:{OCSP_PORT}/ocsp"),
        )
    finally:
        ocsp_responder.stop()
    validate_id_token_info('AuthorizeResponse', response.id_token_info, status='Accepted')
    # Errata 2026-09 (6.3.23): certificateStatus must be Accepted
    assert response.certificate_status == 'Accepted', \
        f"Expected AuthorizeResponse.certificateStatus Accepted, got {response.certificate_status}"
    allowed_energy_transfer_modes = response.allowed_energy_transfer

    # 3. The Test System sends a TransactionEventRequest with
    #    eventType Started
    #    transactionInfo.transactionId <transactionId>
    #    idToken.additionalInfo.additionalIdToken <Configured EVCCID>
    #    idToken.additionalInfo.type EVCCID
    #    The EV is connected, so the request has the EVSE of the transaction (E01.FR.16).
    # 4. The CSMS responds with a TransactionEventResponse
    id_token = {
        'id_token': EMAID_ID_TOKEN,
        'type': 'eMAID',
        'additional_info': [{'additional_id_token': CONFIGURED_EVCCID, 'type': 'EVCCID'}],
    }
    transaction_id = session.start_transaction()
    response = await cp.call(call.TransactionEvent(
        event_type='Started',
        timestamp=utc_now_iso(),
        trigger_reason='Authorized',
        seq_no=session.next_seq_no(),
        transaction_info={'transaction_id': transaction_id},
        id_token=id_token,
        evse={'id': session.evse_id, 'connector_id': session.connector_id},
    ))
    validate_id_token_info('TransactionEventResponse', response.id_token_info, status='Accepted')

    session.state = 'Authorized'
    session.authorized = True
    session.id_token = id_token
    return allowed_energy_transfer_modes, transaction_id
