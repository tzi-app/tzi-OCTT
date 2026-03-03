"""
CSMS (Charging Station Management System) implementation for OCPP 2.0.1 test suite.

Note: This implementation is intended solely for testing, debugging, and stepping through
      the tzi-octt test suite. It is NOT designed to be used in production.
      it was written entirely by Anthropic Claude and OpenAI Codex.

Runs two servers:
  - WS  on port 9000 (Security Profile 1: Basic Auth, no TLS)
  - WSS on port 8082 (Security Profile 2: TLS + Basic Auth, Profile 3: mTLS)

Usage:
  python csms.py [test_mode]

  Examples:
    python csms.py                         # Auto-detect mode (handles all A tests)
    python csms.py password_update         # TC_A_09, A_10
    python csms.py clear_cache             # TC_C_37, C_38
    python csms.py send_local_list_full    # TC_D_01

Test mode configuration (three options, can be combined):

  1. CLI argument (first positional arg):
       python csms.py <test_mode>

  2. Global mode via CSMS_TEST_MODE env var (applies to all CPs):
       CSMS_TEST_MODE=password_update python csms.py

  3. Per-CP mode via CSMS_CP_ACTIONS env var (JSON mapping, takes precedence):
       CSMS_CP_ACTIONS='{"CP001": "password_update"}' python csms.py

  Priority: Per-CP actions > CLI arg / env var.

  When no test mode is set, the CSMS uses auto-detection:
    - Waits briefly after connection to see if CP sends BootNotification
    - If boot is received: no proactive action (quiet connection)
    - If no boot: determines action based on security profile and
      connection sequence (password_update, cert_renewal, profile_upgrade)

Available test modes:
  ""                          Auto-detect / reactive
  "password_update"           SetVariables(BasicAuthPassword)         (TC_A_09, A_10)
  "cert_renewal_cs"           TriggerMessage(SignCSCertificate)       (TC_A_11, A_14)
  "cert_renewal_v2g"          TriggerMessage(SignV2GCertificate)      (TC_A_12)
  "cert_renewal_combined"     TriggerMessage(SignCombinedCertificate) (TC_A_13)
  "profile_upgrade"           SetNetworkProfile + SetVariables + Reset(TC_A_19)
  "clear_cache"               ClearCacheRequest                      (TC_C_37, C_38)
  "get_local_list_version"    GetLocalListVersionRequest              (TC_D_08, D_09)
  "send_local_list_full"      SendLocalList(Full, with entries)       (TC_D_01)
  "send_local_list_diff_update" SendLocalList(Differential, add)      (TC_D_02)
  "send_local_list_diff_remove" SendLocalList(Differential, remove)   (TC_D_03)
  "send_local_list_full_empty"  SendLocalList(Full, empty)            (TC_D_04)

Reactive handlers (always active, no test mode needed):
  - BootNotification, StatusNotification, NotifyEvent, Heartbeat
  - SignCertificate -> CertificateSigned
  - SecurityEventNotification
  - Authorize (token lookup from TOKEN_DATABASE)
  - TransactionEvent (token lookup if id_token present)
  - MeterValues, LogStatusNotification, FirmwareStatusNotification

Token database:
  Hardcoded token entries used by Authorize/TransactionEvent handlers.
  Override group via VALID_TOKEN_GROUP / MASTERPASS_GROUP_ID env vars.

Actions fire only once per CP (except profile_upgrade which uses a state machine).
"""

import asyncio
import json
import logging
import re
import sys
import websockets
import ssl
import base64
import http
import os
from copy import deepcopy
from pathlib import Path
from datetime import datetime, timedelta, timezone

from ocpp.routing import on
from ocpp.v201 import ChargePoint, call, call_result
from ocpp.v201.enums import (
    Action,
    DataTransferStatusEnumType,
    GenericStatusEnumType,
    RegistrationStatusEnumType,
    InstallCertificateUseEnumType,
    GetCertificateIdUseEnumType,
    GetCertificateStatusEnumType,
    Iso15118EVCertificateStatusEnumType,
    MonitoringCriterionEnumType,
    MonitorBaseEnumType,
    MonitorEnumType,
    LogEnumType,
    MessagePriorityEnumType,
    MessageFormatEnumType,
    MessageStateEnumType,
)
from ocpp.v201.datatypes import IdTokenInfoType, IdTokenType
from websockets import ConnectionClosedOK

try:
    from ocpp.exceptions import SecurityError as OCPPSecurityError
except ImportError:
    from ocpp.exceptions import OCPPError
    class OCPPSecurityError(OCPPError):
        code = 'SecurityError'
        default_description = 'Not authorized'

# Keep local imports stable after project restructuring.
_MODULE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _MODULE_DIR.parent
for _path in (str(_MODULE_DIR), str(_PROJECT_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from utils import now_iso

logging.basicConfig(level=logging.INFO)

# ─── Configuration ───────────────────────────────────────────────────────────

REQUIRED_CONFIG_KEYS = (
    'BASIC_AUTH_CP_PASSWORD',
    'NEW_BASIC_AUTH_PASSWORD',
    'CSMS_WS_PORT',
    'CSMS_WSS_PORT',
    'CSMS_TEST_MODE',
    'CSMS_CP_ACTIONS',
    'CSMS_SERVER_CERT',
    'CSMS_SERVER_KEY',
    'CSMS_SERVER_RSA_CERT',
    'CSMS_SERVER_RSA_KEY',
    'CSMS_CA_CERT',
    'CSMS_CA_KEY',
    'CSMS_WSS_URL',
    'CSMS_MESSAGE_TIMEOUT',
    'CSMS_OCPP_INTERFACE',
    'CONFIGURED_EVSE_ID',
    'CONFIGURED_CONNECTOR_ID',
    'CONFIGURED_CONFIGURATION_SLOT',
    'CONFIGURED_SECURITY_PROFILE',
    'CONFIGURED_OCPP_CSMS_URL',
    'CONFIGURED_OCPP_INTERFACE',
    'CONFIGURED_MESSAGE_TIMEOUT',
    'VALID_ID_TOKEN',
    'VALID_ID_TOKEN_TYPE',
    'BASIC_AUTH_CP_F',
    'BASIC_AUTH_CP',
    'CONFIGURED_NUMBER_OF_EVSES',
    'CONFIGURED_CONNECTOR_TYPE',
    'CONFIGURED_VENDOR_ID',
    'CONFIGURED_MESSAGE_ID',
    'CONFIGURED_NUMBER_PHASES',
    'CONFIGURED_STACK_LEVEL',
    'CONFIGURED_CHARGING_RATE_UNIT',
    'CONFIGURED_CHARGING_SCHEDULE_DURATION',
    'TRANSACTION_DURATION',
    'COST_PER_KWH',
    'LOCAL_LIST_VERSION',
    'GROUP_ID',
    'MASTERPASS_GROUP_ID',
    'ISO15118_REVOKED_CERT_HASH_DATA_FILE',
)


def _load_config():
    config_path = Path(__file__).resolve().with_name('config.json')
    if not config_path.exists():
        raise FileNotFoundError(f"Required config file not found: {config_path}")

    with open(config_path) as f:
        loaded = json.load(f)
    if not isinstance(loaded, dict):
        raise ValueError('config.json root must be an object')

    missing = [key for key in REQUIRED_CONFIG_KEYS if key not in loaded]
    if missing:
        raise KeyError(
            "config.json is missing required key(s): " + ", ".join(sorted(missing))
        )
    return loaded


CONFIG = _load_config()


def _cfg_str(key):
    value = CONFIG[key]
    return '' if value is None else str(value)


def _cfg_int(key):
    value = CONFIG[key]
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid int for '{key}' in config.json: {value!r}")


def _cfg_float(key):
    value = CONFIG[key]
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid float for '{key}' in config.json: {value!r}")


def _cfg_dict(key):
    value = CONFIG[key]
    if isinstance(value, dict):
        return value
    raise ValueError(f"Invalid object for '{key}' in config.json: {value!r}")


def _cfg_path(key):
    raw_value = _cfg_str(key)
    if not raw_value:
        return raw_value

    raw_path = Path(raw_value)
    if raw_path.is_absolute():
        return str(raw_path)

    config_dir = Path(__file__).resolve().parent
    candidates = (
        config_dir / raw_path,
        config_dir.parent / raw_path,
        Path.cwd() / raw_path,
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return str((config_dir / raw_path).resolve())


BASIC_AUTH_CP_PASSWORD = _cfg_str('BASIC_AUTH_CP_PASSWORD')
NEW_BASIC_AUTH_PASSWORD = _cfg_str('NEW_BASIC_AUTH_PASSWORD')
WS_PORT = _cfg_int('CSMS_WS_PORT')
WSS_PORT = _cfg_int('CSMS_WSS_PORT')
TEST_MODE = sys.argv[1] if len(sys.argv) > 1 else _cfg_str('CSMS_TEST_MODE')
CP_ACTIONS = _cfg_dict('CSMS_CP_ACTIONS')

# TLS paths (server-side)
SERVER_CERT = _cfg_path('CSMS_SERVER_CERT')
SERVER_KEY = _cfg_path('CSMS_SERVER_KEY')
SERVER_RSA_CERT = _cfg_path('CSMS_SERVER_RSA_CERT')
SERVER_RSA_KEY = _cfg_path('CSMS_SERVER_RSA_KEY')
CA_CERT = _cfg_path('CSMS_CA_CERT')
CA_KEY_PATH = _cfg_path('CSMS_CA_KEY')

# Profile upgrade configuration
CSMS_WSS_URL = _cfg_str('CSMS_WSS_URL')
MESSAGE_TIMEOUT = _cfg_int('CSMS_MESSAGE_TIMEOUT')
OCPP_INTERFACE = _cfg_str('CSMS_OCPP_INTERFACE')

# Provisioning configuration (B tests)
CONFIGURED_EVSE_ID = _cfg_int('CONFIGURED_EVSE_ID')
CONFIGURED_CONNECTOR_ID = _cfg_int('CONFIGURED_CONNECTOR_ID')
CONFIGURED_CONFIGURATION_SLOT = _cfg_int('CONFIGURED_CONFIGURATION_SLOT')
CONFIGURED_SECURITY_PROFILE = _cfg_int('CONFIGURED_SECURITY_PROFILE')
CONFIGURED_OCPP_CSMS_URL = _cfg_str('CONFIGURED_OCPP_CSMS_URL')
CONFIGURED_OCPP_INTERFACE = _cfg_str('CONFIGURED_OCPP_INTERFACE')
CONFIGURED_MESSAGE_TIMEOUT_B = _cfg_int('CONFIGURED_MESSAGE_TIMEOUT')

# F/H-test configuration
VALID_ID_TOKEN = _cfg_str('VALID_ID_TOKEN')
VALID_ID_TOKEN_TYPE = _cfg_str('VALID_ID_TOKEN_TYPE')
BASIC_AUTH_CP_F = _cfg_str('BASIC_AUTH_CP_F')
BASIC_AUTH_CP = _cfg_str('BASIC_AUTH_CP')
CONFIGURED_NUMBER_OF_EVSES = _cfg_int('CONFIGURED_NUMBER_OF_EVSES')
CONFIGURED_CONNECTOR_TYPE = _cfg_str('CONFIGURED_CONNECTOR_TYPE')
CONFIGURED_VENDOR_ID = _cfg_str('CONFIGURED_VENDOR_ID')
CONFIGURED_MESSAGE_ID = _cfg_str('CONFIGURED_MESSAGE_ID')
CONFIGURED_NUMBER_PHASES = _cfg_int('CONFIGURED_NUMBER_PHASES')
CONFIGURED_STACK_LEVEL = _cfg_int('CONFIGURED_STACK_LEVEL')
CONFIGURED_CHARGING_SCHEDULE_DURATION = _cfg_int('CONFIGURED_CHARGING_SCHEDULE_DURATION')
CONFIGURED_CHARGING_RATE_UNIT = (_cfg_str('CONFIGURED_CHARGING_RATE_UNIT') or 'A').upper()
TRANSACTION_DURATION = _cfg_int('TRANSACTION_DURATION')
COST_PER_KWH = _cfg_float('COST_PER_KWH')
LOCAL_LIST_VERSION = _cfg_int('LOCAL_LIST_VERSION')
TRIGGER_PORT = _cfg_int('CSMS_TRIGGER_PORT') if 'CSMS_TRIGGER_PORT' in CONFIG else 5001

# ─── Token Database ──────────────────────────────────────────────────────────

VALID_TOKEN_GROUP = _cfg_str('GROUP_ID')
MASTERPASS_GROUP_ID = _cfg_str('MASTERPASS_GROUP_ID')

TOKEN_DATABASE = {
    '100000C01':       {'status': 'Accepted', 'group': VALID_TOKEN_GROUP},
    '100000C39B':      {'status': 'Accepted', 'group': VALID_TOKEN_GROUP},
    '100000C02':       {'status': 'Invalid'},
    '100000C06':       {'status': 'Blocked'},
    '100000C07':       {'status': 'Expired'},
    'MASTERC47':       {'status': 'Accepted', 'group': MASTERPASS_GROUP_ID},
    'D001001':         {'status': 'Accepted'},
    'D001002':         {'status': 'Accepted'},
    'DE-TZI-C12345-A': {'status': 'Accepted'},
}


def lookup_token(token_value):
    return TOKEN_DATABASE.get(token_value.upper(), {'status': 'Invalid'})


# ─── ISO 15118 Revoked Serials ──────────────────────────────────────────────
# Load serial numbers from the revoked cert hash data file so the Authorize
# handler can distinguish valid from revoked certificates without real OCSP.

_REVOKED_SERIALS = set()
_revoked_file = _cfg_path('ISO15118_REVOKED_CERT_HASH_DATA_FILE')
if _revoked_file and os.path.exists(_revoked_file):
    try:
        with open(_revoked_file) as _f:
            for _entry in json.load(_f):
                _REVOKED_SERIALS.add(_entry['serial_number'])
        logging.info(f"Loaded {len(_REVOKED_SERIALS)} revoked serial(s) from {_revoked_file}")
    except Exception as _e:
        logging.warning(f"Failed to load revoked cert hash data: {_e}")


# ─── Global State ────────────────────────────────────────────────────────────

cp_passwords = {}                # cp_id -> current password
cp_min_security_profile = {}     # cp_id -> minimum required security profile
# Pre-populate SP3 stations so the WSS handler knows to accept them without Basic Auth
for _sp3_id in CONFIG.get('CSMS_SP3_STATION_IDS', []):
    cp_min_security_profile[_sp3_id] = 3
cp_test_state = {}               # cp_id -> test flow state (profile_upgrade)
cp_action_fired = {}             # cp_id -> set of action types already executed

# Auto-detect mode: per-(cp_id, security_profile) action counters
# Tracks how many "no-boot" connections have been handled per profile
_auto_action_counter = {}

# Auto-detect action sequences per security profile.
# These define which proactive action to perform for each successive
# "no-boot" connection (where the CP waits for CSMS-initiated action).
_AUTO_SP1_ACTIONS = ['password_update', 'password_update', 'profile_upgrade']
_AUTO_SP2_ACTIONS = ['cert_renewal_cs', 'profile_upgrade']
_AUTO_SP3_ACTIONS = [
    'cert_renewal_cs',        # TC_A_11
    'cert_renewal_v2g',       # TC_A_12
    'cert_renewal_combined',  # TC_A_13
    'cert_renewal_cs',        # TC_A_14
]

# ─── SP1 Provisioning Sequence ──────────────────────────────────────────────
# Defines the boot response and post-boot action for each successive
# BootNotification received on SP1 (WS) connections.
# Format: (boot_status, action_name_or_None)

_sp1_boot_counter = {}   # cp_id -> boot count on SP1
_auto_detect_used = set()  # CP IDs that have used auto-detect no-boot actions

# Reactive-mode detection: CP IDs that sent non-boot messages (C-test pattern).
# Subsequent "waiting" (silent) connections use C-specific actions (clear_cache)
# instead of A-test actions (password_update, profile_upgrade).
_reactive_mode_detected = set()
_auto_action_counter_c = {}  # Separate counter for C-session SP1 actions
_AUTO_SP1_ACTIONS_C = ['clear_cache', 'clear_cache']

_SP1_PROVISIONING = [
    # Boot/registration
    ('Accepted', None),
    ('Pending', None),
    ('Accepted', None),
    # GetVariables
    ('Accepted', 'get_variables_single'),
    ('Accepted', 'get_variables_multiple'),
    ('Accepted', 'get_variables_split'),
    # SetVariables
    ('Accepted', 'set_variables_single'),
    ('Accepted', 'set_variables_multiple'),
    # GetBaseReport
    ('Accepted', 'get_base_report_config'),
    ('Accepted', 'get_base_report_full'),
    ('Accepted', 'get_base_report_summary'),
    # GetReport with criteria
    ('Accepted', 'get_report_criteria'),
    # Reset CS
    ('Accepted', 'reset_on_idle_cs'),
    ('Accepted', None),
    ('Accepted', 'reset_on_idle_cs'),
    ('Accepted', None),
    ('Accepted', 'reset_immediate_cs'),
    ('Accepted', None),
    # Reset EVSE
    ('Accepted', 'reset_on_idle_evse'),
    ('Accepted', 'reset_on_idle_evse'),
    ('Accepted', 'reset_immediate_evse'),
    # Pending/Rejected flows
    ('Pending', None),
    ('Pending', 'trigger_boot'),
    ('Accepted', None),
    # Network profile
    ('Accepted', 'set_network_profile'),
    ('Accepted', 'set_network_profile'),
]

# E-test transaction tracking and provisioning
# E-mode is detected when a non-boot CP sends 3+ StatusNotification messages,
# distinguishing E tests (many connections with StatusNotification) from C tests
# (only 1-2 StatusNotification before their silent ClearCache tests).
_E_MODE_THRESHOLD = 3
_e_cp_status_count = {}         # cp_id -> StatusNotification count (non-boot only)
_e_mode_active = set()          # CP IDs detected as E-mode
_e_cp_transactions = {}         # cp_id -> latest transaction_id
_e_action_index = {}            # cp_id -> next E provisioning action index
_e_pending_action_task = {}     # cp_id -> asyncio.Task for delayed actions

# E provisioning sequence: (trigger_type, action_name)
#   'after_charging' = fire after TransactionEvent Updated with Charging state + silence
#   'after_ended'    = fire after TransactionEvent Ended with offline=True + silence
#   'silent'         = fire on silent connection (no messages within auto-detect timeout)
_SP1_E_PROVISIONING = [
    ('after_charging', 'request_stop_transaction'),     # E_21
    ('silent', 'get_transaction_status'),                # E_29 reconnect
    ('after_charging', 'get_transaction_status'),        # E_30
    ('after_ended', 'get_transaction_status'),           # E_31 reconnect
    ('silent', 'get_transaction_status_no_id'),          # E_33 reconnect
    ('silent', 'get_transaction_status_no_id'),          # E_34
]

# F-test session detection and provisioning (remote control tests)
_f_mode_active = set()          # CP IDs in F-test mode
_f_action_index = {}            # cp_id -> next action index
_f_pending_action_task = {}     # cp_id -> asyncio.Task for delayed action
_f_remote_start_id = 0          # Global counter for remote start IDs

_SP1_F_PROVISIONING = [
    'request_start_transaction',          # F_01
    'request_start_transaction',          # F_02
    'request_start_transaction',          # F_03
    'request_start_transaction',          # F_04
    'unlock_connector',                   # F_06
    'trigger_meter_values_evse',          # F_11
    'trigger_meter_values_all',           # F_12
    'trigger_transaction_event_evse',     # F_13
    'trigger_transaction_event_all',      # F_14
    'trigger_log_status',                 # F_15
    'trigger_firmware_status',            # F_18
    'trigger_heartbeat',                  # F_20
    'trigger_status_notification_evse',   # F_23
    'trigger_status_notification_evse',   # F_24
    'trigger_heartbeat',                  # F_27
]

# Post-provisioning mode: unified queue for CPs that don't match F session type.
# Contains D (local list) actions followed by G (availability) actions.
# A single global index advances each time any CP fires an action, so
# sequential test suites (D -> G) naturally consume the right actions.
_post_prov_mode_active = set()          # CP IDs in post-provisioning mode
_post_prov_global_index = 0             # Global action index (shared across all CPs)
_post_prov_pending_task = {}            # cp_id -> asyncio.Task for delayed action

_POST_PROVISIONING_ACTIONS = [
    # Local list management (D tests)
    'send_local_list_full',
    'send_local_list_diff_update',
    'send_local_list_diff_remove',
    'send_local_list_full_empty',
    'get_local_list_version',
    'get_local_list_version',
    # Availability management (G tests)
    'change_availability_evse_inoperative',
    'change_availability_evse_operative',
    'change_availability_station_inoperative',
    'change_availability_station_operative',
    'change_availability_connector_inoperative',
    'change_availability_connector_operative',
    'change_availability_evse_inoperative',
    'change_availability_station_inoperative',
    'change_availability_connector_inoperative',
    None,
]

# H-test reservation sequence (CP_1).
_h_reservation_id = 1000
_h_mode_active = set()          # CP IDs in H reservation mode
_h_action_index = {}            # cp_id -> next H action index
_h_pending_action_task = {}     # cp_id -> asyncio.Task for delayed action

_SP1_H_PROVISIONING = [
    'reserve_specific',          # H_01
    'reserve_specific_expiry',   # H_07
    'reserve_unspecified',       # H_08
    'reserve_unspecified_multi', # H_14
    'reserve_connector_type',    # H_15
    'reserve_then_cancel',       # H_17
    'reserve_specific_group',    # H_19
    'reserve_specific',          # H_20
    'reserve_specific',          # H_22
]

# K-test smart charging sequence (CP_1).
# Order matches the lexical test order in ./K when running the full K suite.
_k_mode_active = set()          # CP IDs in K smart-charging mode
_k_action_index = {}            # cp_id -> next K action index
_k_pending_action_task = {}     # cp_id -> asyncio.Task for delayed K action
_k_request_start_id = 0         # RequestStartTransaction remote_start_id counter
_k_profile_id = 5000            # Charging profile id counter for K-mode profiles
_k_latest_transaction_id = {}   # cp_id -> latest known transaction_id
_k_last_offered_schedule = {}   # cp_id -> latest CSMS-offered schedule (for schedule validation)
_k_last_reported_profile_id = {}  # cp_id -> last charging profile id from ReportChargingProfiles
_k_exclusive_mode = set()       # cp_id -> K confirmed, suppress H-mode interference
_k_post_h_reset_done = set()    # cp_id -> K sequence reset once after H suite completion
_active_cp_instance = {}        # cp_id -> currently active ChargePointHandler instance
_trigger_session_active = set() # CP IDs controlled via HTTP trigger API (skip auto-detect)

_SP1_K_PROVISIONING = [
    'set_tx_default_specific',        # K_01
    'set_tx_profile_no_tx',           # K_02
    'set_station_max_profile',        # K_03
    'set_replace_same_id',            # K_04
    'get_then_clear_by_id',           # K_05
    'clear_by_criteria',              # K_06
    'clear_by_criteria',              # K_08
    'set_tx_default_all',             # K_10
    'set_tx_default_specific',        # K_15
    'set_tx_default_recurring',       # K_19
    'get_profiles_evse0_purpose',     # K_29
    'get_profiles_evse_purpose',      # K_30
    'get_profiles_no_evse_purpose',   # K_31
    'get_profiles_by_id',             # K_32
    'get_profiles_evse_stack',        # K_33
    'get_profiles_evse_source',       # K_34
    'get_profiles_evse_purpose',      # K_35
    'get_profiles_evse_purpose_stack',# K_36
    'request_start_tx_with_profile',  # K_37
    'get_composite_evse',             # K_43
    'get_composite_station',          # K_44
    None,                             # K_48 (CP -> CSMS notify only)
    None,                             # K_50 (CP -> CSMS notify only)
    None,                             # K_51 (CP -> CSMS notify only)
    None,                             # K_52 (triggered by NotifyChargingLimit)
    None,                             # K_53 (NotifyEVChargingNeeds-driven)
    None,                             # K_55 (NotifyEVChargingNeeds-driven)
    None,                             # K_57 (NotifyEVChargingNeeds-driven)
    None,                             # K_58 (CSMS-initiated renegotiation after charging event)
    None,                             # K_59 (CSMS-initiated + NotifyEVChargingNeeds-driven)
    None,                             # K_60 (ongoing transaction-driven TxProfile)
    None,                             # K_70 (ongoing transaction-driven multiple profiles)
]

# L-test firmware management sequence (CP_1).
# This models a CSMS firmware campaign plan that progresses per maintenance
# session and reacts to CP firmware status notifications.
_l_mode_active = set()          # CP IDs in L firmware-management mode
_l_action_index = {}            # cp_id -> next L action index (raw, no wrap)
_l_pending_action_task = {}     # cp_id -> asyncio.Task for delayed L action

_SP1_L_PROVISIONING = [
    {'op': 'update', 'variant': 'secure'},                     # L_01
    {'op': 'update', 'variant': 'install_scheduled'},          # L_02
    {'op': 'update', 'variant': 'download_scheduled'},         # L_03
    {'op': 'update', 'variant': 'secure'},                     # L_04
    {'op': 'update', 'variant': 'secure'},                     # L_05
    {'op': 'update', 'variant': 'secure'},                     # L_06
    {'op': 'update', 'variant': 'secure'},                     # L_07
    {'op': 'update', 'variant': 'secure'},                     # L_08
    {'op': 'update', 'variant': 'secure'},                     # L_09
    {'op': 'update', 'variant': 'replace_on_downloading'},     # L_10
    {'op': 'update', 'variant': 'replace_on_downloading'},     # L_11
    {'op': 'update', 'variant': 'secure'},                     # L_13
    {'op': 'publish', 'variant': 'standard'},                  # L_17
    {'op': 'publish', 'variant': 'standard'},                  # L_19
    {'op': 'publish', 'variant': 'standard'},                  # L_20
    {'op': 'unpublish', 'variant': 'standard'},                # L_21
    {'op': 'unpublish', 'variant': 'standard'},                # L_22
    {'op': 'unpublish', 'variant': 'standard'},                # L_23
    {'op': 'publish', 'variant': 'standard'},                  # L_24
]

# M-test certificate-management sequence (CP_1).
# This models a CSMS certificate campaign that includes certificate
# installation, retrieval, and deletion, followed by reactive-only
# certificate status and EV certificate exchange flows.
_m_mode_active = set()          # CP IDs in M certificate-management mode
_m_action_index = {}            # cp_id -> next M action index (raw, no wrap)
_m_pending_action_task = {}     # cp_id -> asyncio.Task for delayed M action
_m_last_cert_hash_data = {}     # cp_id -> last certificate hash data from GetInstalledCertificateIds

_SP1_M_PROVISIONING = [
    {'op': 'install_certificate', 'install_type': InstallCertificateUseEnumType.csms_root_certificate},             # M_01
    {'op': 'install_certificate', 'install_type': InstallCertificateUseEnumType.manufacturer_root_certificate},     # M_02
    {'op': 'install_certificate', 'install_type': InstallCertificateUseEnumType.v2g_root_certificate},              # M_03
    {'op': 'install_certificate', 'install_type': InstallCertificateUseEnumType.mo_root_certificate},               # M_04
    {'op': 'install_certificate', 'install_type': InstallCertificateUseEnumType.csms_root_certificate},             # M_05
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.csms_root_certificate], 'repeat': 3},  # M_12
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.manufacturer_root_certificate]},   # M_13
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.v2g_root_certificate]},            # M_14
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.v2g_certificate_chain]},           # M_15
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.mo_root_certificate]},             # M_16
    {
        'op': 'get_installed_ids',
        'certificate_type': [
            GetCertificateIdUseEnumType.csms_root_certificate,
            GetCertificateIdUseEnumType.manufacturer_root_certificate,
        ],
    },                                                                                                              # M_17
    {'op': 'get_installed_ids', 'certificate_type': None},                                                          # M_18
    {'op': 'get_installed_ids', 'certificate_type': [GetCertificateIdUseEnumType.manufacturer_root_certificate]},  # M_19
    {'op': 'install_get_delete', 'install_type': InstallCertificateUseEnumType.csms_root_certificate, 'certificate_type': [GetCertificateIdUseEnumType.csms_root_certificate]},  # M_20 SHA256
    {'op': 'install_get_delete', 'install_type': InstallCertificateUseEnumType.csms_root_certificate, 'certificate_type': [GetCertificateIdUseEnumType.csms_root_certificate]},  # M_20 SHA384
    {'op': 'install_get_delete', 'install_type': InstallCertificateUseEnumType.csms_root_certificate, 'certificate_type': [GetCertificateIdUseEnumType.csms_root_certificate]},  # M_20 SHA512
    {'op': 'install_get_delete', 'install_type': InstallCertificateUseEnumType.csms_root_certificate, 'certificate_type': [GetCertificateIdUseEnumType.csms_root_certificate]},  # M_21
    None,                                                                                                            # M_24 (CP initiated)
    None,                                                                                                            # M_26 (CP initiated)
    None,                                                                                                            # M_28 (CP initiated)
]

# N-test diagnostics/monitoring/customer-information sequence (CP_1).
# This models a CSMS monitoring and diagnostics campaign with proactive and
# reactive phases.
_n_mode_active = set()          # CP IDs in N diagnostics/monitoring mode
_n_action_index = {}            # cp_id -> next N action index (raw, no wrap)
_n_pending_action_task = {}     # cp_id -> asyncio.Task for delayed N action

_N_LOG_REMOTE_LOCATION = 'https://logs.example.org/upload'
_N_CUSTOMER_CERTIFICATE_HASH = {
    'hash_algorithm': 'SHA256',
    'issuer_name_hash': 'aabbccdd' * 8,
    'issuer_key_hash': 'eeff0011' * 8,
    'serial_number': '01020304',
}

_SP1_N_PROVISIONING = [
    {  # N_01
        'op': 'get_monitoring_report_pair',
        'first': {'monitoring_criteria': [MonitoringCriterionEnumType.delta_monitoring]},
        'second': {'monitoring_criteria': [MonitoringCriterionEnumType.threshold_monitoring]},
    },
    {  # N_02
        'op': 'get_monitoring_report_pair',
        'first': {
            'component_variable': [
                {'component': {'name': 'ChargingStation'}, 'variable': {'name': 'Power'}},
            ],
        },
        'second': {
            'component_variable': [
                {'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}}, 'variable': {'name': 'AvailabilityState'}},
            ],
        },
    },
    {  # N_03
        'op': 'get_monitoring_report_pair',
        'first': {
            'monitoring_criteria': [MonitoringCriterionEnumType.delta_monitoring],
            'component_variable': [
                {'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}}, 'variable': {'name': 'AvailabilityState'}},
            ],
        },
        'second': {
            'monitoring_criteria': [MonitoringCriterionEnumType.threshold_monitoring],
            'component_variable': [
                {'component': {'name': 'ChargingStation'}, 'variable': {'name': 'Power'}},
            ],
        },
    },
    {  # N_05
        'op': 'set_monitoring_base_sequence',
        'bases': [
            MonitorBaseEnumType.all,
            MonitorBaseEnumType.factory_default,
            MonitorBaseEnumType.hard_wired_only,
        ],
    },
    {  # N_08
        'op': 'set_variable_monitoring',
        'data': [
            {
                'value': 1,
                'type': MonitorEnumType.delta,
                'severity': 8,
                'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}},
                'variable': {'name': 'AvailabilityState'},
            },
        ],
    },
    {  # N_09
        'op': 'set_variable_monitoring',
        'data': [
            {
                'value': 1,
                'type': MonitorEnumType.delta,
                'severity': 8,
                'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}},
                'variable': {'name': 'AvailabilityState'},
            },
            {
                'value': 1,
                'type': MonitorEnumType.delta,
                'severity': 8,
                'component': {'name': 'ChargingStation'},
                'variable': {'name': 'AvailabilityState'},
            },
        ],
    },
    {'op': 'set_monitoring_level', 'severity': 4},  # N_16
    {'op': 'set_monitoring_level', 'severity': 4},  # N_17
    {'op': 'clear_variable_monitoring_chunked', 'ids': [1, 2, 3, 4, 5]},  # N_18
    None,  # N_21 (CP initiated NotifyEvent)
    None,  # N_24 (CP initiated NotifyEvent)
    {'op': 'get_log', 'log_type': LogEnumType.diagnostics_log},  # N_25
    {'op': 'customer_information', 'report': True, 'clear': False, 'ref': 'id_token'},  # N_27
    {'op': 'customer_information', 'report': True, 'clear': False, 'ref': 'id_token'},  # N_28
    {'op': 'customer_information', 'report': True, 'clear': False, 'ref': 'id_token'},  # N_29
    {'op': 'customer_information', 'report': True, 'clear': True, 'ref': 'id_token'},  # N_30
    {'op': 'customer_information', 'report': True, 'clear': True, 'ref': 'id_token'},  # N_31
    {'op': 'customer_information', 'report': False, 'clear': True, 'ref': 'id_token'},  # N_32
    {'op': 'get_log', 'log_type': LogEnumType.diagnostics_log},  # N_34
    {'op': 'get_log', 'log_type': LogEnumType.security_log},  # N_35
    {'op': 'get_log_dual', 'log_type': LogEnumType.diagnostics_log},  # N_36
    {'op': 'clear_variable_monitoring', 'ids': [1]},  # N_44
    {'op': 'customer_information', 'report': True, 'clear': True, 'ref': 'id_token', 'send_local_list_on_notify': True},  # N_46
    {'op': 'get_monitoring_report', 'monitoring_criteria': None, 'component_variable': None},  # N_47
    None,  # N_48 (CP initiated NotifyEvent)
    None,  # N_49 (CP initiated NotifyEvent)
    None,  # N_50 (CP initiated NotifyEvent)
    {  # N_60
        'op': 'get_monitoring_report_pair',
        'first': {
            'monitoring_criteria': [MonitoringCriterionEnumType.delta_monitoring],
            'component_variable': [
                {'component': {'name': 'ChargingStation'}, 'variable': {'name': 'AvailabilityState'}},
                {'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}}, 'variable': {'name': 'AvailabilityState'}},
            ],
        },
        'second': {
            'monitoring_criteria': [MonitoringCriterionEnumType.threshold_monitoring],
            'component_variable': [
                {'component': {'name': 'ChargingStation'}, 'variable': {'name': 'AvailabilityState'}},
                {'component': {'name': 'EVSE', 'evse': {'id': CONFIGURED_EVSE_ID}}, 'variable': {'name': 'AvailabilityState'}},
            ],
        },
    },
    {'op': 'customer_information', 'report': True, 'clear': True, 'ref': 'customer_identifier'},  # N_62
    {'op': 'customer_information', 'report': True, 'clear': True, 'ref': 'customer_certificate'},  # N_63
]

# O-test display-message-management sequence (CP_1).
# This models a CSMS display-message campaign with message set/get/clear
# requests and reactive handling for NotifyDisplayMessages.
_o_mode_active = set()          # CP IDs in O display-message mode
_o_action_index = {}            # cp_id -> next O action index (raw, no wrap)
_o_pending_action_task = {}     # cp_id -> asyncio.Task for delayed O action
_o_message_id = 9000            # message id counter for O-mode display messages

_SP1_O_PROVISIONING = [
    {'op': 'set_display'},  # O_01
    {'op': 'set_then_get', 'filter': 'all'},  # O_02
    {'op': 'get_display', 'filter': 'all'},  # O_03
    {'op': 'set_then_clear', 'clear_known': True},  # O_04
    {'op': 'clear_display_unknown'},  # O_05
    {'op': 'set_display', 'transaction_ref': 'active'},  # O_06
    {'op': 'set_then_get', 'filter': 'id'},  # O_07
    {'op': 'set_then_get', 'filter': 'priority'},  # O_08
    {'op': 'set_then_get', 'filter': 'state'},  # O_09
    {'op': 'set_display', 'transaction_ref': 'unknown'},  # O_10
    {'op': 'set_then_get', 'filter': 'unknown_id'},  # O_11
    {'op': 'set_replace_same_id'},  # O_12
    {'op': 'set_display', 'start_offset_s': 60},  # O_13
    {'op': 'set_display', 'end_offset_s': 120},  # O_14
    {'op': 'set_display', 'priority': MessagePriorityEnumType.always_front},  # O_17
    {'op': 'set_display', 'state': MessageStateEnumType.faulted},  # O_18
    {'op': 'set_display', 'format': MessageFormatEnumType.html},  # O_19
    {'op': 'set_display', 'state': MessageStateEnumType.charging},  # O_25
    {'op': 'set_display', 'priority': MessagePriorityEnumType.normal_cycle},  # O_26
    {  # O_27
        'op': 'set_display',
        'transaction_ref': 'active',
        'include_state': False,
        'start_offset_s': 60,
        'include_end': False,
    },
    {  # O_28
        'op': 'set_display',
        'transaction_ref': 'active',
        'include_state': False,
        'include_start': False,
        'end_offset_s': 120,
    },
]

_L_UPDATE_LOCATION = 'https://downloads.example.org/firmware/ocpp-v201.bin'
_L_UPDATE_LOCATION_ALT = 'https://downloads.example.org/firmware/ocpp-v201-hotfix.bin'
_L_PUBLISH_LOCATION = 'https://cdn.example.org/firmware/publish.bin'
_L_PUBLISH_CHECKSUM = 'A1B2C3D4'
_L_UNPUBLISH_CHECKSUM = 'A1B2C3D4'
_L_SIGNING_CERT = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIBlTCCATugAwIBAgIUBtziLTestSigningCert1234567890wCgYIKoZIzj0EAwIw\n"
    "GDEWMBQGA1UEAwwNT0NQUC1GaXJtd2FyZS1DQTAeFw0yNTAxMDEwMDAwMDBaFw0z\n"
    "NTAxMDEwMDAwMDBaMBgxFjAUBgNVBAMMDU9DUFAtRmlybXdhcmUtQ0EwWTATBgcq\n"
    "hkjOPQIBBggqhkjOPQMBBwNCAAQxL2vJ3I9+u8V6n8a+Pj8f1R+MdC5y2t3N2q1J\n"
    "kL5rX9YyKqS8gLJ5v6s8n1Z4u8X9A3mQz4fL0p1gR0sN8a8Lo1MwUTAdBgNVHQ4E\n"
    "FgQURRANDOMPLACEHOLDERFIRMWARECERT123wHwYDVR0jBBgwFoAURRANDOMPLACE\n"
    "HOLDERFIRMWARECERT123MA8GA1UdEwEB/wQFMAMBAf8wCgYIKoZIzj0EAwIDSQAw\n"
    "RgIhAJs6U2FMtR6eD4lJQz8J2kTq8n0A5Q9Jw3eV2D1sL0h7AiEAxqW+QWm3Q+vB\n"
    "6w8A7nZ5o2o4C7N3d9mQ2nQxQ9rY5n8=\n"
    "-----END CERTIFICATE-----"
)
_L_SIGNATURE = 'MEUCIQCfirmwareSignaturePlaceholder1234567890=='

_M_CERTIFICATE_PEM = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIBZjCCAQ2gAwIBAgIUY2VydGlmaWNhdGVUZXN0TTAxMDAwMDAwCgYIKoZIzj0E\n"
    "AwIwGTEXMBUGA1UEAwwOTUNTVE1vY2tSb290Q0EwHhcNMjYwMTAxMDAwMDAwWhcN\n"
    "MzYwMTAxMDAwMDAwWjAZMRcwFQYDVQQDDA5NQ1NUTW9ja1Jvb3RDQTBZMBMGByqG\n"
    "SM49AgEGCCqGSM49AwEHA0IABFhE3V6g1uZs2M4m2V7g3X9q+P5c1w6s8A4zKz3I\n"
    "qv9j5Y3w4k9y2fN6a8d2n0h1Q0xW8z8w8n6n2u9M0VdWq5CjUzBRMB0GA1UdDgQW\n"
    "BBRtb2NrY2VydGlmaWNhdGVzaWduZXIwHwYDVR0jBBgwFoAUbW9ja2NlcnRpZmlj\n"
    "YXRlc2lnbmVyMA8GA1UdEwEB/wQFMAMBAf8wCgYIKoZIzj0EAwIDSAAwRQIgQ0hB\n"
    "UkdJTkdfU1RBVElPTl9URVNUX01PQ0tfQ0VSVC0wAiAQVklfVGVzdF9DZXJ0X0RhdGE=\n"
    "-----END CERTIFICATE-----"
)

_M_OCSP_RESULT_B64 = base64.b64encode(b"\x30\x03\x0a\x01\x00").decode("ascii")
_M_EXI_RESPONSE_B64 = base64.b64encode(b"mock-iso15118-exi-response").decode("ascii")

# I/J transaction cost tracking: cp_id -> tx_id -> {'start': float, 'last': float}
_txn_cost_state = {}


def _enum_text(value):
    return getattr(value, 'value', str(value))


def _normalize_data_transfer_key(value):
    return str(value or '').strip().lower()


def _transaction_id_from_info(transaction_info):
    if isinstance(transaction_info, dict):
        return transaction_info.get('transaction_id') or transaction_info.get('transactionId')
    return getattr(transaction_info, 'transaction_id', None) or getattr(transaction_info, 'transactionId', None)


def _charging_state_from_info(transaction_info):
    if isinstance(transaction_info, dict):
        return transaction_info.get('charging_state') or transaction_info.get('chargingState', '')
    return getattr(transaction_info, 'charging_state', '') or getattr(transaction_info, 'chargingState', '')


def _extract_last_meter_value(meter_value):
    """Extract the last numeric sampled value from meter_value payload."""
    if not meter_value:
        return None
    last_numeric = None
    for mv in meter_value:
        if isinstance(mv, dict):
            sampled_values = mv.get('sampled_value') or mv.get('sampledValue') or []
        else:
            sampled_values = getattr(mv, 'sampled_value', []) or []
        for sample in sampled_values:
            if isinstance(sample, dict):
                raw_value = sample.get('value')
            else:
                raw_value = getattr(sample, 'value', None)
            if raw_value is None:
                continue
            try:
                last_numeric = float(raw_value)
            except (TypeError, ValueError):
                continue
    return last_numeric


def _update_transaction_cost_state(cp_id, transaction_id, meter_value):
    meter_reading = _extract_last_meter_value(meter_value)
    if transaction_id is None or meter_reading is None:
        return
    cp_map = _txn_cost_state.setdefault(cp_id, {})
    tx_state = cp_map.setdefault(transaction_id, {'start': meter_reading, 'last': meter_reading})
    tx_state['last'] = meter_reading


def _estimate_transaction_total_cost(cp_id, transaction_id):
    tx_state = _txn_cost_state.get(cp_id, {}).get(transaction_id)
    if not tx_state:
        return 0.0
    delta_wh = max(0.0, float(tx_state['last']) - float(tx_state['start']))
    return round((delta_wh / 1000.0) * COST_PER_KWH, 2)


async def _send_cost_updated(cp, transaction_id):
    total_cost = _estimate_transaction_total_cost(cp.id, transaction_id)
    try:
        logging.info(f"Sending CostUpdated to {cp.id}: txn={transaction_id}, total_cost={total_cost}")
        await cp.call(call.CostUpdated(total_cost=total_cost, transaction_id=transaction_id))
    except Exception as e:
        logging.warning(f"CostUpdated call failed for {cp.id}: {e}")


# ─── K-Mode Smart Charging Helpers ───────────────────────────────────────────

def _k_next_request_start_id():
    global _k_request_start_id
    _k_request_start_id += 1
    return _k_request_start_id


def _k_next_profile_id():
    global _k_profile_id
    _k_profile_id += 1
    return _k_profile_id


def _k_allocate_session_index(cp_id):
    raw_idx = _k_action_index.get(cp_id, 0)
    if _SP1_K_PROVISIONING:
        idx = raw_idx % len(_SP1_K_PROVISIONING)
    else:
        idx = 0
    _k_action_index[cp_id] = raw_idx + 1
    if raw_idx != idx:
        logging.info(
            f"K-mode session index wrapped for {cp_id}: raw_index={raw_idx}, wrapped_index={idx}"
        )
    return idx


def _h_allocate_session_index(cp_id):
    raw_idx = _h_action_index.get(cp_id, 0)
    if _SP1_H_PROVISIONING:
        idx = raw_idx % len(_SP1_H_PROVISIONING)
    else:
        idx = 0
    _h_action_index[cp_id] = raw_idx + 1
    if raw_idx != idx:
        logging.info(
            f"H-mode session index wrapped for {cp_id}: raw_index={raw_idx}, wrapped_index={idx}"
        )
    return idx


def _l_allocate_session_index(cp_id):
    raw_idx = _l_action_index.get(cp_id, 0)
    if raw_idx >= len(_SP1_L_PROVISIONING):
        logging.info(
            f"L-mode sequence exhausted for {cp_id}: raw_index={raw_idx}, "
            f"total={len(_SP1_L_PROVISIONING)}"
        )
        return -1
    _l_action_index[cp_id] = raw_idx + 1
    return raw_idx


def _m_allocate_session_index(cp_id):
    raw_idx = _m_action_index.get(cp_id, 0)
    if raw_idx >= len(_SP1_M_PROVISIONING):
        logging.info(
            f"M-mode sequence exhausted for {cp_id}: raw_index={raw_idx}, "
            f"total={len(_SP1_M_PROVISIONING)}"
        )
        return -1
    _m_action_index[cp_id] = raw_idx + 1
    return raw_idx


def _n_allocate_session_index(cp_id):
    raw_idx = _n_action_index.get(cp_id, 0)
    if raw_idx >= len(_SP1_N_PROVISIONING):
        logging.info(
            f"N-mode sequence exhausted for {cp_id}: raw_index={raw_idx}, "
            f"total={len(_SP1_N_PROVISIONING)}"
        )
        return -1
    _n_action_index[cp_id] = raw_idx + 1
    return raw_idx


def _o_allocate_session_index(cp_id):
    raw_idx = _o_action_index.get(cp_id, 0)
    if raw_idx >= len(_SP1_O_PROVISIONING):
        logging.info(
            f"O-mode sequence exhausted for {cp_id}: raw_index={raw_idx}, "
            f"total={len(_SP1_O_PROVISIONING)}"
        )
        return -1
    _o_action_index[cp_id] = raw_idx + 1
    return raw_idx


def _l_session_index(cp):
    return getattr(cp, '_l_session_index', _l_action_index.get(cp.id, -1))


def _m_session_index(cp):
    return getattr(cp, '_m_session_index', _m_action_index.get(cp.id, -1))


def _n_session_index(cp):
    return getattr(cp, '_n_session_index', _n_action_index.get(cp.id, -1))


def _o_session_index(cp):
    return getattr(cp, '_o_session_index', _o_action_index.get(cp.id, -1))


def _l_future_iso(seconds):
    return (
        datetime.now(timezone.utc) + timedelta(seconds=max(1, int(seconds)))
    ).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _l_build_update_firmware_payload(*, variant='secure', alternate=False):
    # retrieveDateTime is mandatory in FirmwareType.
    retrieve_date_time = _l_future_iso(120 if variant == 'download_scheduled' else 10)
    payload = {
        'location': _L_UPDATE_LOCATION_ALT if alternate else _L_UPDATE_LOCATION,
        'retrieve_date_time': retrieve_date_time,
        'signing_certificate': _L_SIGNING_CERT,
        'signature': _L_SIGNATURE,
    }
    if variant == 'install_scheduled':
        payload['install_date_time'] = _l_future_iso(120)
    return payload


async def _l_send_update_firmware(cp, *, variant='secure', alternate=False):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    request_id = _next_request_id()
    firmware = _l_build_update_firmware_payload(variant=variant, alternate=alternate)
    try:
        logging.info(
            f"L-mode: sending UpdateFirmware to {cp.id} "
            f"(request_id={request_id}, variant={variant}, alternate={alternate})"
        )
        await cp.call(call.UpdateFirmware(
            request_id=request_id,
            firmware=firmware,
            retries=1,
            retry_interval=5,
        ))
        return request_id
    except Exception as e:
        logging.warning(f"L-mode UpdateFirmware failed for {cp.id}: {e}")
        return None


async def _l_send_publish_firmware(cp):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    request_id = _next_request_id()
    try:
        logging.info(
            f"L-mode: sending PublishFirmware to {cp.id} "
            f"(request_id={request_id}, location={_L_PUBLISH_LOCATION})"
        )
        await cp.call(call.PublishFirmware(
            location=_L_PUBLISH_LOCATION,
            checksum=_L_PUBLISH_CHECKSUM,
            request_id=request_id,
            retries=1,
            retry_interval=5,
        ))
        return request_id
    except Exception as e:
        logging.warning(f"L-mode PublishFirmware failed for {cp.id}: {e}")
        return None


async def _l_send_unpublish_firmware(cp):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    try:
        logging.info(
            f"L-mode: sending UnpublishFirmware to {cp.id} "
            f"(checksum={_L_UNPUBLISH_CHECKSUM})"
        )
        await cp.call(call.UnpublishFirmware(checksum=_L_UNPUBLISH_CHECKSUM))
    except Exception as e:
        logging.warning(f"L-mode UnpublishFirmware failed for {cp.id}: {e}")


def _k_period(limit):
    period = {
        'start_period': 0,
        'limit': float(limit),
    }
    if CONFIGURED_NUMBER_PHASES != 3:
        period['number_phases'] = CONFIGURED_NUMBER_PHASES
    return period


def _k_schedule(limit, *, include_start_schedule=True, duration=None, rate_unit=None):
    schedule = {
        'id': 1,
        'charging_rate_unit': rate_unit or CONFIGURED_CHARGING_RATE_UNIT,
        'duration': duration if duration is not None else CONFIGURED_CHARGING_SCHEDULE_DURATION,
        'charging_schedule_period': [_k_period(limit)],
    }
    if include_start_schedule:
        schedule['start_schedule'] = now_iso()
    return schedule


def _k_profile(profile_id, purpose, kind, limit, *, include_start_schedule=True,
               include_valid_window=False, recurrency_kind=None, transaction_id=None):
    profile = {
        'id': profile_id,
        'stack_level': CONFIGURED_STACK_LEVEL,
        'charging_profile_purpose': purpose,
        'charging_profile_kind': kind,
        'charging_schedule': [
            _k_schedule(limit, include_start_schedule=include_start_schedule),
        ],
    }
    if include_valid_window:
        profile['valid_from'] = now_iso()
        profile['valid_to'] = (
            datetime.now(timezone.utc) + timedelta(seconds=CONFIGURED_CHARGING_SCHEDULE_DURATION)
        ).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    if recurrency_kind is not None:
        profile['recurrency_kind'] = recurrency_kind
    if transaction_id is not None:
        profile['transaction_id'] = str(transaction_id)
    return profile


def _k_extract_schedule(profile):
    if not isinstance(profile, dict):
        return None
    schedules = profile.get('charging_schedule') or profile.get('chargingSchedule')
    if isinstance(schedules, list) and schedules:
        return schedules[0]
    if isinstance(schedules, dict):
        return schedules
    return None


def _k_extract_profile_id(charging_profile):
    if isinstance(charging_profile, list) and charging_profile:
        first = charging_profile[0]
    else:
        first = charging_profile
    if isinstance(first, dict):
        return first.get('id')
    return getattr(first, 'id', None)


def _k_extract_period_limits(schedule):
    if not schedule:
        return []
    if isinstance(schedule, dict):
        periods = schedule.get('charging_schedule_period') or schedule.get('chargingSchedulePeriod') or []
    else:
        periods = getattr(schedule, 'charging_schedule_period', None) or []
    limits = []
    for period in periods:
        if isinstance(period, dict):
            raw = period.get('limit')
        else:
            raw = getattr(period, 'limit', None)
        try:
            limits.append(float(raw))
        except (TypeError, ValueError):
            continue
    return limits


def _k_schedule_exceeds_offer(cp_id, proposed_schedule):
    offered = _k_last_offered_schedule.get(cp_id)
    if offered is None:
        return False
    offered_limits = _k_extract_period_limits(offered)
    proposed_limits = _k_extract_period_limits(proposed_schedule)
    if not offered_limits or not proposed_limits:
        return False
    for idx, proposed_limit in enumerate(proposed_limits):
        offered_limit = offered_limits[min(idx, len(offered_limits) - 1)]
        if proposed_limit > offered_limit + 1e-9:
            return True
    return False


def _k_session_index(cp):
    return getattr(cp, '_k_session_index', _k_action_index.get(cp.id, -1))


async def _k_send_set_charging_profile(cp, evse_id, profile):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    try:
        logging.info(
            f"K-mode: sending SetChargingProfile to {cp.id} "
            f"(evse_id={evse_id}, purpose={profile.get('charging_profile_purpose')}, "
            f"profile_id={profile.get('id')})"
        )
        response = await cp.call(call.SetChargingProfile(evse_id=evse_id, charging_profile=profile))
        # CALLERROR may be surfaced as a response object instead of an exception
        # depending on the ocpp stack internals. Treat such responses as failure.
        if response is None or hasattr(response, 'error_code'):
            raise RuntimeError(f"SetChargingProfile unsuccessful response: {response!r}")
        # Once K traffic is accepted for a CP, suppress H-mode for that CP to
        # avoid cross-suite action races (H ReserveNow can cancel pending K timers).
        if cp.id not in _k_exclusive_mode:
            _k_exclusive_mode.add(cp.id)
            _h_mode_active.discard(cp.id)
            logging.info(f"K-mode confirmed for {cp.id}; H-mode suppressed for this CP")
        if profile.get('charging_profile_purpose') == 'TxProfile':
            offered = _k_extract_schedule(profile)
            if offered is not None:
                _k_last_offered_schedule[cp.id] = deepcopy(offered)
    except Exception as e:
        if _active_cp_instance.get(cp.id) is not cp:
            return
        logging.warning(f"K-mode SetChargingProfile failed for {cp.id}: {e}")
        # Support standalone K34 run: if very first K action can't be handled
        # and we don't observe reservation-flow messages, jump to K34 query.
        if _k_session_index(cp) == 0:
            if cp._k_standalone_fallback_task:
                cp._k_standalone_fallback_task.cancel()
            cp._k_standalone_fallback_task = asyncio.create_task(
                _k_standalone_fallback_to_k34(cp)
            )
            return
        error_text = str(e)
        if 'NotImplemented' in error_text or 'No handler for SetChargingProfile' in error_text:
            _k_mode_active.discard(cp.id)
            logging.info(f"K-mode disabled for {cp.id} (SetChargingProfile not supported)")


async def _k_send_tx_profile_for_transaction(cp, transaction_id, *, limit=16.0):
    if not transaction_id:
        logging.warning(f"K-mode: cannot send TxProfile for {cp.id} without transaction_id")
        return
    profile = _k_profile(
        _k_next_profile_id(),
        'TxProfile',
        'Absolute',
        limit,
        include_start_schedule=True,
        transaction_id=str(transaction_id),
    )
    await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile)


async def _k_send_get_charging_profiles(cp, criterion, *, evse_id=None):
    request_id = _next_request_id()
    try:
        logging.info(
            f"K-mode: sending GetChargingProfiles to {cp.id} "
            f"(request_id={request_id}, evse_id={evse_id}, criterion={criterion})"
        )
        kwargs = {
            'request_id': request_id,
            'charging_profile': criterion,
        }
        if evse_id is not None:
            kwargs['evse_id'] = evse_id
        await cp.call(call.GetChargingProfiles(**kwargs))
        return True
    except Exception as e:
        logging.warning(f"K-mode GetChargingProfiles failed for {cp.id}: {e}")
        return False


async def _k_send_clear_charging_profile(cp, *, charging_profile_id=None, criteria=None):
    try:
        logging.info(
            f"K-mode: sending ClearChargingProfile to {cp.id} "
            f"(charging_profile_id={charging_profile_id}, criteria={criteria})"
        )
        kwargs = {}
        if charging_profile_id is not None:
            kwargs['charging_profile_id'] = charging_profile_id
        if criteria is not None:
            kwargs['charging_profile_criteria'] = criteria
        await cp.call(call.ClearChargingProfile(**kwargs))
    except Exception as e:
        logging.warning(f"K-mode ClearChargingProfile failed for {cp.id}: {e}")


async def _k_send_get_composite_schedule(cp, *, evse_id):
    try:
        logging.info(
            f"K-mode: sending GetCompositeSchedule to {cp.id} "
            f"(evse_id={evse_id}, duration={CONFIGURED_CHARGING_SCHEDULE_DURATION})"
        )
        await cp.call(call.GetCompositeSchedule(
            duration=CONFIGURED_CHARGING_SCHEDULE_DURATION,
            evse_id=evse_id,
            charging_rate_unit=CONFIGURED_CHARGING_RATE_UNIT,
        ))
    except Exception as e:
        logging.warning(f"K-mode GetCompositeSchedule failed for {cp.id}: {e}")


async def _k_standalone_fallback_to_k34(cp, delay=3):
    """Fallback for standalone K34 runs where SetChargingProfile isn't implemented.

    If no reservation-flow evidence appears shortly after K action #0 failure,
    switch to K34 action and send GetChargingProfiles(chargingLimitSource).
    """
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if cp._h_confirmed:
            return
        if _k_session_index(cp) != 0:
            return
        logging.info(f"K-mode standalone fallback for {cp.id}: switching to K34 action")
        cp._k_session_index = 15
        cp._k_action_fired_for_session = True
        await _execute_k_action(cp, 'get_profiles_evse_source')
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"K-mode standalone fallback failed for {cp.id}: {e}")


# ─── Per-CP Test Mode ───────────────────────────────────────────────────────

def get_test_mode_for_cp(cp_id):
    """Get the test mode for a specific charge point.
    Per-CP mapping (CSMS_CP_ACTIONS) takes precedence over global TEST_MODE.
    """
    if CP_ACTIONS:
        return CP_ACTIONS.get(cp_id, '')
    return TEST_MODE


# ─── Certificate Signing ─────────────────────────────────────────────────────

def sign_csr_with_ca(csr_pem_str):
    """Sign a CSR with our CA and return the certificate chain as PEM string."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization

    with open(CA_CERT, 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(CA_KEY_PATH, 'rb') as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    csr = x509.load_pem_x509_csr(csr_pem_str.encode())
    now = datetime.now(timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=365))
        .sign(ca_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode()
    return cert_pem + ca_pem


# ─── ChargePoint Handler ─────────────────────────────────────────────────────

class ChargePointHandler(ChargePoint):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Skip schema validation so CSMS accepts non-standard fields (e.g. Cash token type)
        for action, handlers in self.route_map.items():
            handlers['_skip_schema_validation'] = True
        self._boot_received = asyncio.Event()
        self._any_message_received = asyncio.Event()
        self._security_profile = 1
        self._boot_status = None
        self._f_action_fired_for_session = False
        self._post_prov_action_fired_for_session = False
        self._h_action_fired_for_session = False
        self._h_session_index = -1
        self._k_action_fired_for_session = False
        self._k_session_index = -1
        self._k_pending_clear_from_report = False
        self._k_schedule_rejected_once = False
        self._k_renegotiation_pending = False
        self._k_initiated_set_sent = False
        self._k_tx_profile_sent = False
        self._k_multi_profile_sent = False
        self._l_action_fired_for_session = False
        self._l_session_index = -1
        self._l_flow_state = None
        self._m_action_fired_for_session = False
        self._m_session_index = -1
        self._m_last_certificate_hash_data = None
        self._n_action_fired_for_session = False
        self._n_session_index = -1
        self._n_flow_state = None
        self._o_action_fired_for_session = False
        self._o_session_index = -1
        self._o_flow_state = None
        self._o_last_display_message = None
        self._o_display_messages = {}
        self._h_confirmed = False
        self._k_standalone_fallback_task = None
        self._k_index_rolled_back = False
        # I/J detection: if these appear early in session, do not force H-mode.
        self._seen_authorize = False
        self._seen_transaction_event = False
        self._seen_meter_values = False

    async def route_message(self, raw_msg):
        """Override to track when any message is received from this CP."""
        self._any_message_received.set()
        # Cancel any pending E-mode delayed action (new message = CP is still active)
        if self.id in _e_pending_action_task:
            _e_pending_action_task.pop(self.id).cancel()
        # Cancel any pending F-mode delayed action (new message = CP is still sending)
        if self.id in _f_pending_action_task:
            _f_pending_action_task.pop(self.id).cancel()
        # Cancel any pending post-provisioning action (new message = CP is still sending)
        if self.id in _post_prov_pending_task:
            _post_prov_pending_task.pop(self.id).cancel()
        # Cancel any pending H-mode action (new message = CP is still sending)
        if self.id in _h_pending_action_task:
            _h_pending_action_task.pop(self.id).cancel()
        # Cancel any pending K-mode action (new message = CP is still sending)
        if self.id in _k_pending_action_task:
            _k_pending_action_task.pop(self.id).cancel()
        # Cancel any pending L-mode action (new message = CP is still sending)
        if self.id in _l_pending_action_task:
            _l_pending_action_task.pop(self.id).cancel()
        # Cancel any pending M-mode action (new message = CP is still sending)
        if self.id in _m_pending_action_task:
            _m_pending_action_task.pop(self.id).cancel()
        # Cancel any pending N-mode action (new message = CP is still sending)
        if self.id in _n_pending_action_task:
            _n_pending_action_task.pop(self.id).cancel()
        # Cancel any pending O-mode action (new message = CP is still sending)
        if self.id in _o_pending_action_task:
            _o_pending_action_task.pop(self.id).cancel()
        result = await super().route_message(raw_msg)
        # Reschedule F-mode action after message processing (silence detection)
        if self.id in _f_mode_active and not self._f_action_fired_for_session:
            idx = _f_action_index.get(self.id, 0)
            if idx < len(_SP1_F_PROVISIONING):
                _f_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_f_action(self, idx)
                )
        # Reschedule post-provisioning action (silence detection)
        if self.id in _post_prov_mode_active and not self._post_prov_action_fired_for_session:
            idx = _post_prov_global_index
            if idx < len(_POST_PROVISIONING_ACTIONS):
                action = _POST_PROVISIONING_ACTIONS[idx]
                if action is not None:
                    _post_prov_pending_task[self.id] = asyncio.create_task(
                        _delayed_post_prov_action(self)
                    )
        # Reschedule H-mode action (silence detection)
        if self.id in _h_mode_active and self.id not in _k_exclusive_mode and not self._h_action_fired_for_session:
            idx = self._h_session_index
            if 0 <= idx < len(_SP1_H_PROVISIONING):
                _h_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_h_action(self, idx)
                )
        # Reschedule K-mode action (silence detection).
        # Once a CP is classified as K-mode, keep K actions active even if the
        # session includes Authorize/TransactionEvent traffic (e.g. K_29+).
        if self.id in _k_mode_active and not self._k_action_fired_for_session:
            idx = self._k_session_index
            if 0 <= idx < len(_SP1_K_PROVISIONING):
                _k_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_k_action(self, idx)
                )
        # Reschedule L-mode action (silence detection).
        if self.id in _l_mode_active and not self._l_action_fired_for_session:
            idx = self._l_session_index
            if 0 <= idx < len(_SP1_L_PROVISIONING):
                _l_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_l_action(self, idx)
                )
        # Reschedule M-mode action (silence detection).
        if self.id in _m_mode_active and not self._m_action_fired_for_session:
            idx = self._m_session_index
            if 0 <= idx < len(_SP1_M_PROVISIONING):
                _m_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_m_action(self, idx)
                )
        # Reschedule N-mode action (silence detection).
        if self.id in _n_mode_active and not self._n_action_fired_for_session:
            idx = self._n_session_index
            if 0 <= idx < len(_SP1_N_PROVISIONING):
                _n_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_n_action(self, idx)
                )
        # Reschedule O-mode action (silence detection).
        if self.id in _o_mode_active and not self._o_action_fired_for_session:
            idx = self._o_session_index
            if 0 <= idx < len(_SP1_O_PROVISIONING):
                _o_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_o_action(self, idx)
                )
        return result

    @on(Action.boot_notification)
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        logging.info(f"BootNotification from {self.id}: reason={reason}")
        self._boot_received.set()

        # Trigger-controlled pending boot: respond Pending when set via HTTP API
        if cp_test_state.get(self.id) == 'pending_boot':
            self._boot_status = 'Pending'
            logging.info(f"Trigger-controlled pending boot for {self.id}: Pending")
            return call_result.BootNotification(
                current_time=now_iso(),
                interval=1,
                status=RegistrationStatusEnumType.pending,
            )

        # Determine boot response from SP1 provisioning sequence
        # (only when auto-detect no-boot actions have NOT been used,
        # i.e., this is a provisioning-focused session like B tests).
        # SP1 provisioning only applies to WS (non-TLS) connections.
        # WSS connections rely on trigger API for test actions.
        if self._security_profile == 1 and self.id not in _auto_detect_used:
            # Post-provisioning mode: always Accepted, action triggered by silence
            if self.id in _post_prov_mode_active:
                self._boot_status = 'Accepted'
                logging.info(f"Post-provisioning boot for {self.id}: Accepted")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # F-mode: always Accepted, action triggered by silence detection
            if self.id in _f_mode_active:
                self._boot_status = 'Accepted'
                logging.info(f"F-mode boot for {self.id}: Accepted")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # H-mode: always Accepted, action triggered by silence detection
            if self.id in _h_mode_active and _h_action_index.get(self.id, 0) >= len(_SP1_H_PROVISIONING):
                _h_mode_active.discard(self.id)
            if self.id in _h_mode_active and self.id not in _k_exclusive_mode:
                self._h_session_index = _h_allocate_session_index(self.id)
                self._boot_status = 'Accepted'
                logging.info(f"H-mode boot for {self.id}: Accepted")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # Transition from K to L when K campaign has been consumed.
            if (
                self.id in _k_mode_active
                and _k_action_index.get(self.id, 0) >= len(_SP1_K_PROVISIONING)
            ):
                _k_mode_active.discard(self.id)
                if _l_action_index.get(self.id, 0) < len(_SP1_L_PROVISIONING):
                    _l_mode_active.add(self.id)
                    logging.info(f"L-mode transition for {self.id}: K campaign exhausted")

            # Transition from L to M when L campaign has been consumed.
            if (
                self.id in _l_mode_active
                and _l_action_index.get(self.id, 0) >= len(_SP1_L_PROVISIONING)
            ):
                _l_mode_active.discard(self.id)
                if _m_action_index.get(self.id, 0) < len(_SP1_M_PROVISIONING):
                    _m_mode_active.add(self.id)
                    logging.info(f"M-mode transition for {self.id}: L campaign exhausted")

            # Transition from M to N when M campaign has been consumed.
            if (
                self.id in _m_mode_active
                and _m_action_index.get(self.id, 0) >= len(_SP1_M_PROVISIONING)
            ):
                _m_mode_active.discard(self.id)
                if _n_action_index.get(self.id, 0) < len(_SP1_N_PROVISIONING):
                    _n_mode_active.add(self.id)
                    logging.info(f"N-mode transition for {self.id}: M campaign exhausted")

            # Transition from N to O when N campaign has been consumed.
            if (
                self.id in _n_mode_active
                and _n_action_index.get(self.id, 0) >= len(_SP1_N_PROVISIONING)
            ):
                _n_mode_active.discard(self.id)
                if _o_action_index.get(self.id, 0) < len(_SP1_O_PROVISIONING):
                    _o_mode_active.add(self.id)
                    logging.info(f"O-mode transition for {self.id}: N campaign exhausted")

            # L-mode: always Accepted, action triggered by silence detection.
            if self.id in _l_mode_active:
                self._boot_status = 'Accepted'
                reason_text = _enum_text(reason)
                if reason_text == 'FirmwareUpdate':
                    # In-session reboot during firmware installation.
                    logging.info(f"L-mode boot for {self.id}: Accepted (firmware reboot)")
                else:
                    self._l_session_index = _l_allocate_session_index(self.id)
                    logging.info(
                        f"L-mode boot for {self.id}: Accepted "
                        f"(session_index={self._l_session_index})"
                    )
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # M-mode: always Accepted, action triggered by silence detection.
            if self.id in _m_mode_active and _m_action_index.get(self.id, 0) >= len(_SP1_M_PROVISIONING):
                _m_mode_active.discard(self.id)
            if self.id in _m_mode_active:
                self._m_session_index = _m_allocate_session_index(self.id)
                self._boot_status = 'Accepted'
                logging.info(f"M-mode boot for {self.id}: Accepted (session_index={self._m_session_index})")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # N-mode: always Accepted, action triggered by silence detection.
            if self.id in _n_mode_active and _n_action_index.get(self.id, 0) >= len(_SP1_N_PROVISIONING):
                _n_mode_active.discard(self.id)
            if self.id in _n_mode_active:
                self._n_session_index = _n_allocate_session_index(self.id)
                self._boot_status = 'Accepted'
                logging.info(f"N-mode boot for {self.id}: Accepted (session_index={self._n_session_index})")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # O-mode: always Accepted, action triggered by silence detection.
            if self.id in _o_mode_active and _o_action_index.get(self.id, 0) >= len(_SP1_O_PROVISIONING):
                _o_mode_active.discard(self.id)
            if self.id in _o_mode_active:
                self._o_session_index = _o_allocate_session_index(self.id)
                self._o_display_messages = {}
                self._o_last_display_message = None
                self._boot_status = 'Accepted'
                logging.info(f"O-mode boot for {self.id}: Accepted (session_index={self._o_session_index})")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # CP_1 after H completion: stay Accepted and let session detection
            # choose between I/J reactive behavior and campaign modes.
            if (
                self.id == BASIC_AUTH_CP
                and _h_action_index.get(self.id, 0) >= len(_SP1_H_PROVISIONING)
                and self.id not in _k_mode_active
                and self.id not in _l_mode_active
                and self.id not in _m_mode_active
                and self.id not in _n_mode_active
                and self.id not in _o_mode_active
            ):
                self._boot_status = 'Accepted'
                asyncio.create_task(self._detect_session_type())
                logging.info(f"Post-H boot for {self.id}: Accepted (mode detection pending)")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # K-mode: always Accepted, action triggered by silence detection
            if self.id in _k_mode_active:
                self._k_session_index = _k_allocate_session_index(self.id)
                self._boot_status = 'Accepted'
                logging.info(f"K-mode boot for {self.id}: Accepted (session_index={self._k_session_index})")
                return call_result.BootNotification(
                    current_time=now_iso(),
                    interval=10,
                    status=RegistrationStatusEnumType.accepted,
                )

            # B-mode: use standard provisioning list
            counter = _sp1_boot_counter.get(self.id, 0)
            _sp1_boot_counter[self.id] = counter + 1

            if counter < len(_SP1_PROVISIONING):
                boot_status, action = _SP1_PROVISIONING[counter]
            else:
                boot_status, action = ('Accepted', None)

            self._boot_status = boot_status
            interval = 1 if boot_status in ('Pending', 'Rejected') else 10

            if action:
                asyncio.create_task(self._execute_provisioning(action))

            # First boot with no action: schedule session type detection
            if counter == 0 and action is None and boot_status == 'Accepted':
                asyncio.create_task(self._detect_session_type())

            logging.info(f"SP1 provisioning boot #{counter}: {boot_status}, action={action}")
            return call_result.BootNotification(
                current_time=now_iso(),
                interval=interval,
                status=getattr(RegistrationStatusEnumType, boot_status.lower()),
            )

        # Non-SP1 boots: always Accepted
        self._boot_status = 'Accepted'
        return call_result.BootNotification(
            current_time=now_iso(),
            interval=10,
            status=RegistrationStatusEnumType.accepted
        )

    async def _detect_session_type(self):
        """Detect the session type after the first boot.

        After the first boot with Accepted + no action, wait briefly.
        If no second boot has arrived (B tests would have reconnected by now),
        determine session type:
        - F-mode: CP ID matches BASIC_AUTH_CP_F (remote control tests)
        - Post-provisioning: default for all other CPs (unified D + G queue)
        """
        await asyncio.sleep(4)  # B_01 disconnects quickly; D/F/G stay connected

        # Already detected (shouldn't happen, but be safe)
        if self.id in _post_prov_mode_active:
            logging.info(f"Session detection: already post-prov mode for {self.id}")
            return
        if self.id in _f_mode_active:
            logging.info(f"Session detection: already F-mode for {self.id}")
            return
        if self.id in _h_mode_active:
            logging.info(f"Session detection: already H-mode for {self.id}")
            return
        if self.id in _k_mode_active:
            logging.info(f"Session detection: already K-mode for {self.id}")
            return
        if self.id in _l_mode_active:
            logging.info(f"Session detection: already L-mode for {self.id}")
            return
        if self.id in _m_mode_active:
            logging.info(f"Session detection: already M-mode for {self.id}")
            return
        if self.id in _n_mode_active:
            logging.info(f"Session detection: already N-mode for {self.id}")
            return
        if self.id in _o_mode_active:
            logging.info(f"Session detection: already O-mode for {self.id}")
            return

        h_progress = _h_action_index.get(self.id, 0) if self.id == BASIC_AUTH_CP else 0

        # Check if a second boot has been received (B-test pattern)
        boot_count = _sp1_boot_counter.get(self.id, 0)
        if boot_count > 1 and not (
            self.id == BASIC_AUTH_CP and h_progress >= len(_SP1_H_PROVISIONING)
        ):
            logging.info(f"Session detection: second boot already arrived for {self.id} - B session")
            return

        # Check if connection is still open
        if not self._connection.open:
            logging.info(f"Session detection: connection closed for {self.id} - B session")
            return

        # When H sequence is already exhausted for CP_1, restart K sequencing once
        # so subsequent standalone K sessions start deterministically from K_01.
        if self.id == BASIC_AUTH_CP:
            if h_progress >= len(_SP1_H_PROVISIONING) and self.id not in _k_post_h_reset_done:
                prev_k = _k_action_index.get(self.id, 0)
                _k_action_index[self.id] = 0
                _k_post_h_reset_done.add(self.id)
                logging.info(
                    f"K-mode sequence reset for {self.id} after H completion "
                    f"(previous_raw_index={prev_k})"
                )

        # No second boot and still connected: determine session type
        if BASIC_AUTH_CP_F and self.id == BASIC_AUTH_CP_F:
            # F-mode: remote control test session
            _f_mode_active.add(self.id)
            _f_action_index.setdefault(self.id, 0)
            logging.info(f"F-mode detected for {self.id} - scheduling first F action")
            idx = _f_action_index[self.id]
            if idx < len(_SP1_F_PROVISIONING):
                _f_pending_action_task[self.id] = asyncio.create_task(
                    _delayed_f_action(self, idx)
                )
            return

        # I/J style session on CP_1: reactive only, no proactive actions.
        if self.id == BASIC_AUTH_CP and h_progress >= len(_SP1_H_PROVISIONING) and (
            self._seen_authorize or self._seen_transaction_event or self._seen_meter_values
        ):
            logging.info(f"I/J reactive session detected for {self.id} - no proactive action")
            return

        # H-mode: reservation test session
        if BASIC_AUTH_CP and self.id == BASIC_AUTH_CP:
            if h_progress < len(_SP1_H_PROVISIONING):
                _h_mode_active.add(self.id)
                self._h_session_index = _h_allocate_session_index(self.id)
                idx = self._h_session_index
                logging.info(f"H-mode detected for {self.id} - scheduling H action #{idx}")
                if 0 <= idx < len(_SP1_H_PROVISIONING):
                    _h_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_h_action(self, idx)
                    )
                return

            _h_mode_active.discard(self.id)
            k_progress = _k_action_index.get(self.id, 0)
            if k_progress < len(_SP1_K_PROVISIONING):
                # H exhausted: switch to K-mode for subsequent CP_1 sessions.
                _k_mode_active.add(self.id)
                self._k_session_index = _k_allocate_session_index(self.id)
                k_idx = self._k_session_index
                logging.info(f"K-mode detected for {self.id} - scheduling K action #{k_idx}")
                if 0 <= k_idx < len(_SP1_K_PROVISIONING):
                    _k_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_k_action(self, k_idx)
                    )
                return

            l_progress = _l_action_index.get(self.id, 0)
            if l_progress < len(_SP1_L_PROVISIONING):
                _k_mode_active.discard(self.id)
                _l_mode_active.add(self.id)
                self._l_session_index = _l_allocate_session_index(self.id)
                l_idx = self._l_session_index
                logging.info(f"L-mode detected for {self.id} - scheduling L action #{l_idx}")
                if 0 <= l_idx < len(_SP1_L_PROVISIONING):
                    _l_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_l_action(self, l_idx)
                    )
                return

            m_progress = _m_action_index.get(self.id, 0)
            if m_progress < len(_SP1_M_PROVISIONING):
                _l_mode_active.discard(self.id)
                _m_mode_active.add(self.id)
                self._m_session_index = _m_allocate_session_index(self.id)
                m_idx = self._m_session_index
                logging.info(f"M-mode detected for {self.id} - scheduling M action #{m_idx}")
                if 0 <= m_idx < len(_SP1_M_PROVISIONING):
                    _m_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_m_action(self, m_idx)
                    )
                return

            n_progress = _n_action_index.get(self.id, 0)
            if n_progress < len(_SP1_N_PROVISIONING):
                _m_mode_active.discard(self.id)
                _n_mode_active.add(self.id)
                self._n_session_index = _n_allocate_session_index(self.id)
                n_idx = self._n_session_index
                logging.info(f"N-mode detected for {self.id} - scheduling N action #{n_idx}")
                if 0 <= n_idx < len(_SP1_N_PROVISIONING):
                    _n_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_n_action(self, n_idx)
                    )
                return

            o_progress = _o_action_index.get(self.id, 0)
            if o_progress < len(_SP1_O_PROVISIONING):
                _n_mode_active.discard(self.id)
                _o_mode_active.add(self.id)
                self._o_session_index = _o_allocate_session_index(self.id)
                o_idx = self._o_session_index
                logging.info(f"O-mode detected for {self.id} - scheduling O action #{o_idx}")
                if 0 <= o_idx < len(_SP1_O_PROVISIONING):
                    _o_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_o_action(self, o_idx)
                    )
                return

        # Default: post-provisioning mode (unified D + G action queue)
        _post_prov_mode_active.add(self.id)
        idx = _post_prov_global_index
        logging.info(f"Post-provisioning mode detected for {self.id} - scheduling action #{idx}")
        if idx < len(_POST_PROVISIONING_ACTIONS) and _POST_PROVISIONING_ACTIONS[idx] is not None:
            _post_prov_pending_task[self.id] = asyncio.create_task(
                _delayed_post_prov_action(self)
            )

    async def _execute_provisioning(self, action):
        """Execute a provisioning action after a short delay."""
        await asyncio.sleep(2)
        try:
            await _dispatch_provisioning(self, action)
        except Exception as e:
            logging.warning(f"Provisioning action '{action}' failed for {self.id}: {e}")

    @on(Action.status_notification)
    async def on_status_notification(self, **kwargs):
        if self._boot_status in ('Pending', 'Rejected'):
            logging.info(f"StatusNotification from {self.id} rejected (boot={self._boot_status})")
            raise OCPPSecurityError('Not authorized during Pending/Rejected state')
        connector_status = _enum_text(kwargs.get('connector_status') or kwargs.get('connectorStatus') or '')
        if connector_status and connector_status != 'Available':
            self._h_confirmed = True
        # E-mode detection: count StatusNotifications from non-boot CPs
        if not self._boot_received.is_set():
            _e_cp_status_count[self.id] = _e_cp_status_count.get(self.id, 0) + 1
            if _e_cp_status_count[self.id] >= _E_MODE_THRESHOLD:
                _e_mode_active.add(self.id)
        logging.info(f"StatusNotification from {self.id}: {kwargs}")
        return call_result.StatusNotification()

    @on(Action.notify_event)
    async def on_notify_event(self, **kwargs):
        if self._boot_status in ('Pending', 'Rejected'):
            logging.info(f"NotifyEvent from {self.id} rejected (boot={self._boot_status})")
            raise OCPPSecurityError('Not authorized during Pending/Rejected state')
        logging.info(f"NotifyEvent from {self.id}")
        return call_result.NotifyEvent()

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        return call_result.Heartbeat(current_time=now_iso())

    @on(Action.sign_certificate)
    async def on_sign_certificate(self, csr, certificate_type=None, **kwargs):
        logging.info(f"SignCertificateRequest from {self.id}: type={certificate_type}")
        asyncio.create_task(self._send_certificate_signed(csr, certificate_type))
        return call_result.SignCertificate(status=GenericStatusEnumType.accepted)

    async def _send_certificate_signed(self, csr_pem, certificate_type):
        """Sign the CSR and send CertificateSignedRequest back to the CP."""
        await asyncio.sleep(0.5)
        try:
            cert_chain = sign_csr_with_ca(csr_pem)
            logging.info(f"Sending CertificateSignedRequest to {self.id} "
                         f"(chain length={len(cert_chain)})")
            await self.call(call.CertificateSigned(
                certificate_chain=cert_chain,
                certificate_type=certificate_type,
            ))
        except Exception as e:
            logging.error(f"Failed to send CertificateSignedRequest to {self.id}: {e}")

    @on(Action.authorize)
    async def on_authorize(self, id_token, certificate=None,
                           iso15118_certificate_hash_data=None, **kwargs):
        self._seen_authorize = True
        token_value = id_token.get('id_token', '') if isinstance(id_token, dict) else str(id_token)
        token_info = lookup_token(token_value)
        logging.info(f"Authorize from {self.id}: token={token_value} -> {token_info['status']}")

        id_token_info = {'status': token_info['status']}
        if 'group' in token_info:
            id_token_info['group_id_token'] = {
                'id_token': token_info['group'], 'type': 'Central'
            }

        response_kwargs = {'id_token_info': id_token_info}

        if iso15118_certificate_hash_data or certificate:
            # Check if any certificate in the hash data is revoked
            revoked = False
            if iso15118_certificate_hash_data:
                for hash_entry in iso15118_certificate_hash_data:
                    serial = (hash_entry.get('serial_number', '')
                              if isinstance(hash_entry, dict)
                              else getattr(hash_entry, 'serial_number', ''))
                    if serial in _REVOKED_SERIALS:
                        revoked = True
                        break
            if revoked:
                response_kwargs['certificate_status'] = 'CertificateRevoked'
                id_token_info['status'] = 'Invalid'
                logging.info(f"Certificate revoked for {self.id}")
            else:
                response_kwargs['certificate_status'] = 'Accepted'

        return call_result.Authorize(**response_kwargs)

    @on(Action.transaction_event)
    async def on_transaction_event(self, event_type, timestamp, trigger_reason,
                                   seq_no, transaction_info, id_token=None,
                                   evse=None, **kwargs):
        self._seen_transaction_event = True
        event_type_text = _enum_text(event_type)
        trigger_reason_text = _enum_text(trigger_reason)
        txn_id = _transaction_id_from_info(transaction_info)
        if txn_id is not None:
            txn_id = str(txn_id)
            _k_latest_transaction_id[self.id] = txn_id
        charging_state = _charging_state_from_info(transaction_info)
        meter_value = kwargs.get('meter_value')
        _update_transaction_cost_state(self.id, txn_id, meter_value)

        # E-mode transaction tracking
        if self.id in _e_mode_active and transaction_info is not None:
            if txn_id:
                _e_cp_transactions[self.id] = txn_id
            charging_state = _charging_state_from_info(transaction_info)
            offline = kwargs.get('offline', False)

            idx = _e_action_index.get(self.id, 0)
            if idx < len(_SP1_E_PROVISIONING):
                trigger, action = _SP1_E_PROVISIONING[idx]
                if trigger == 'after_charging' and str(charging_state) == 'Charging':
                    _e_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_e_action(self, action, idx))
                elif trigger == 'after_ended' and event_type_text == 'Ended' and offline:
                    _e_pending_action_task[self.id] = asyncio.create_task(
                        _delayed_e_action(self, action, idx))

        response_kwargs = {}
        if id_token:
            token_value = (id_token.get('id_token', '')
                           if isinstance(id_token, dict) else str(id_token))
            token_info = lookup_token(token_value)
            logging.info(f"TransactionEvent from {self.id}: token={token_value} -> {token_info['status']}")
            group_id_token = None
            if 'group' in token_info:
                group_id_token = IdTokenType(
                    id_token=token_info['group'], type='Central'
                )
            response_kwargs['id_token_info'] = IdTokenInfoType(
                status=token_info['status'],
                group_id_token=group_id_token,
            )
        else:
            logging.info(f"TransactionEvent from {self.id}: type={event_type} trigger={trigger_reason}")

        # I_01: if no totalCost in TransactionEventResponse, send CostUpdated for periodic meter updates.
        if event_type_text == 'Updated' and trigger_reason_text == 'MeterValuePeriodic' and txn_id:
            asyncio.create_task(_send_cost_updated(self, txn_id))

        # I_02: totalCost must be present on Ended transaction response.
        if event_type_text == 'Ended':
            response_kwargs['total_cost'] = _estimate_transaction_total_cost(self.id, txn_id)

        # K-mode transaction-driven actions (K_58, K_59, K_60, K_70, K_55 renegotiation).
        if self.id in _k_mode_active:
            asyncio.create_task(
                _k_handle_transaction_event(
                    self,
                    event_type_text=event_type_text,
                    trigger_reason_text=trigger_reason_text,
                    charging_state_text=_enum_text(charging_state),
                    transaction_id=txn_id,
                )
            )
        if self.id in _o_mode_active:
            asyncio.create_task(
                _o_handle_transaction_event(
                    self,
                    transaction_id=txn_id,
                )
            )

        return call_result.TransactionEvent(**response_kwargs)

    @on(Action.notify_report)
    async def on_notify_report(self, request_id, generated_at, seq_no, tbc=False,
                                report_data=None, **kwargs):
        logging.info(f"NotifyReport from {self.id}: request_id={request_id}, seq_no={seq_no}")
        return call_result.NotifyReport()

    @on(Action.report_charging_profiles)
    async def on_report_charging_profiles(self, request_id, charging_limit_source,
                                          charging_profile, evse_id=None, tbc=False, **kwargs):
        logging.info(
            f"ReportChargingProfiles from {self.id}: request_id={request_id}, "
            f"evse_id={evse_id}, source={charging_limit_source}, tbc={tbc}"
        )
        reported_id = _k_extract_profile_id(charging_profile)
        if reported_id is not None:
            _k_last_reported_profile_id[self.id] = reported_id
        if self._k_pending_clear_from_report:
            self._k_pending_clear_from_report = False
            target_id = _k_last_reported_profile_id.get(self.id)
            if target_id is not None:
                asyncio.create_task(
                    _k_send_clear_charging_profile(self, charging_profile_id=target_id)
                )
        return call_result.ReportChargingProfiles()

    @on(Action.notify_ev_charging_needs)
    async def on_notify_ev_charging_needs(self, charging_needs, evse_id, max_schedule_tuples=None, **kwargs):
        logging.info(
            f"NotifyEVChargingNeeds from {self.id}: evse_id={evse_id}, "
            f"session_index={_k_session_index(self)}"
        )
        idx = _k_session_index(self)
        if self.id in _k_mode_active and idx in (25, 26, 27, 28, 29):
            txn_id = _k_latest_transaction_id.get(self.id)
            asyncio.create_task(_k_send_tx_profile_for_transaction(self, txn_id))
        return call_result.NotifyEVChargingNeeds(status='Accepted')

    @on(Action.notify_ev_charging_schedule)
    async def on_notify_ev_charging_schedule(self, time_base, charging_schedule, evse_id, **kwargs):
        idx = _k_session_index(self)
        status = GenericStatusEnumType.accepted
        if self.id in _k_mode_active and idx == 26:
            # K_55: first schedule exceeds offered limits -> Rejected, then renegotiate.
            if _k_schedule_exceeds_offer(self.id, charging_schedule) and not self._k_schedule_rejected_once:
                self._k_schedule_rejected_once = True
                self._k_renegotiation_pending = True
                status = GenericStatusEnumType.rejected
        logging.info(
            f"NotifyEVChargingSchedule from {self.id}: evse_id={evse_id}, "
            f"session_index={idx}, status={status}"
        )
        return call_result.NotifyEVChargingSchedule(status=status)

    @on(Action.notify_charging_limit)
    async def on_notify_charging_limit(self, charging_limit, **kwargs):
        idx = _k_session_index(self)
        logging.info(
            f"NotifyChargingLimit from {self.id}: session_index={idx}, charging_limit={charging_limit}"
        )
        if self.id in _k_mode_active and idx == 24:
            criterion = {'charging_profile_purpose': 'ChargingStationExternalConstraints'}
            asyncio.create_task(
                _k_send_get_charging_profiles(self, criterion, evse_id=CONFIGURED_EVSE_ID)
            )
        return call_result.NotifyChargingLimit()

    @on(Action.cleared_charging_limit)
    async def on_cleared_charging_limit(self, charging_limit_source, **kwargs):
        logging.info(f"ClearedChargingLimit from {self.id}: source={charging_limit_source}")
        return call_result.ClearedChargingLimit()

    @on(Action.security_event_notification)
    async def on_security_event_notification(self, type, timestamp, **kwargs):
        logging.info(f"SecurityEventNotification from {self.id}: type={type}")
        return call_result.SecurityEventNotification()

    @on(Action.meter_values)
    async def on_meter_values(self, evse_id, meter_value, **kwargs):
        self._seen_meter_values = True
        logging.info(f"MeterValues from {self.id}: evse_id={evse_id}")
        return call_result.MeterValues()

    @on(Action.log_status_notification)
    async def on_log_status_notification(self, status, request_id=None, **kwargs):
        logging.info(f"LogStatusNotification from {self.id}: status={status}, request_id={request_id}")
        if self.id in _n_mode_active and self._n_flow_state is not None:
            asyncio.create_task(
                _n_handle_log_status(
                    self,
                    status_text=_enum_text(status),
                    request_id=request_id,
                )
            )
        return call_result.LogStatusNotification()

    @on(Action.notify_monitoring_report)
    async def on_notify_monitoring_report(self, request_id, seq_no, generated_at,
                                          monitor=None, tbc=False, **kwargs):
        logging.info(
            f"NotifyMonitoringReport from {self.id}: "
            f"request_id={request_id}, seq_no={seq_no}, tbc={tbc}"
        )
        return call_result.NotifyMonitoringReport()

    @on(Action.notify_customer_information)
    async def on_notify_customer_information(self, data, seq_no, generated_at,
                                             request_id, tbc=False, **kwargs):
        logging.info(
            f"NotifyCustomerInformation from {self.id}: "
            f"request_id={request_id}, seq_no={seq_no}, tbc={tbc}"
        )
        if self.id in _n_mode_active and self._n_flow_state is not None:
            asyncio.create_task(
                _n_handle_notify_customer_information(self, request_id=request_id)
            )
        return call_result.NotifyCustomerInformation()

    @on(Action.notify_display_messages)
    async def on_notify_display_messages(self, request_id, message_info=None, tbc=False, **kwargs):
        logging.info(
            f"NotifyDisplayMessages from {self.id}: "
            f"request_id={request_id}, tbc={tbc}"
        )
        return call_result.NotifyDisplayMessages()

    @on(Action.data_transfer)
    async def on_data_transfer(self, vendor_id, message_id=None, data=None, **kwargs):
        # Keep P-flow reconnects in reactive mode instead of SP1 boot-state
        # progression (Accepted -> Pending -> ...), which is specific to B flows.
        if self._security_profile == 1:
            _sp1_boot_counter[self.id] = 0
        configured_vendor = _normalize_data_transfer_key(CONFIGURED_VENDOR_ID or 'tzi.app')
        configured_message = _normalize_data_transfer_key(CONFIGURED_MESSAGE_ID or 'TestMessage')
        request_vendor = _normalize_data_transfer_key(vendor_id)
        request_message = _normalize_data_transfer_key(message_id)

        if request_vendor != configured_vendor:
            status = DataTransferStatusEnumType.unknown_vendor_id
        elif configured_message and request_message != configured_message:
            status = DataTransferStatusEnumType.unknown_message_id
        else:
            # CSMS has no vendor-specific extension implementation; reject known keys.
            status = DataTransferStatusEnumType.rejected

        logging.info(
            f"DataTransfer from {self.id}: vendor_id={vendor_id!r}, "
            f"message_id={message_id!r}, status={status}"
        )
        return call_result.DataTransfer(status=status)

    @on(Action.publish_firmware_status_notification)
    async def on_publish_firmware_status_notification(self, status, location=None, request_id=None, **kwargs):
        logging.info(
            f"PublishFirmwareStatusNotification from {self.id}: "
            f"status={status}, request_id={request_id}, location={location}"
        )
        return call_result.PublishFirmwareStatusNotification()

    @on(Action.firmware_status_notification)
    async def on_firmware_status_notification(self, status, request_id=None, **kwargs):
        logging.info(
            f"FirmwareStatusNotification from {self.id}: "
            f"status={status}, request_id={request_id}"
        )
        if self.id in _l_mode_active and self._l_flow_state is not None:
            asyncio.create_task(
                _l_handle_firmware_status(self, status_text=_enum_text(status), request_id=request_id)
            )
        return call_result.FirmwareStatusNotification()

    @on(Action.reservation_status_update)
    async def on_reservation_status_update(self, reservation_id, reservation_update_status, **kwargs):
        self._h_confirmed = True
        logging.info(
            f"ReservationStatusUpdate from {self.id}: "
            f"reservation_id={reservation_id}, reservation_update_status={reservation_update_status}"
        )
        return call_result.ReservationStatusUpdate()

    @on(Action.get_certificate_status)
    async def on_get_certificate_status(self, ocsp_request_data, **kwargs):
        logging.info(f"GetCertificateStatus from {self.id}: ocsp_request_data={ocsp_request_data}")
        return call_result.GetCertificateStatus(
            status=GetCertificateStatusEnumType.accepted,
            ocsp_result=_M_OCSP_RESULT_B64,
        )

    @on(Action.get_15118_ev_certificate)
    async def on_get_15118_ev_certificate(self, iso15118_schema_version, action, exi_request, **kwargs):
        logging.info(
            f"Get15118EVCertificate from {self.id}: "
            f"schema={iso15118_schema_version}, action={action}"
        )
        return call_result.Get15118EVCertificate(
            status=Iso15118EVCertificateStatusEnumType.accepted,
            exi_response=_M_EXI_RESPONSE_B64,
        )


# ─── Provisioning Actions (SP1 post-boot) ────────────────────────────────────

_prov_request_id = 0

def _next_request_id():
    global _prov_request_id
    _prov_request_id += 1
    return _prov_request_id


async def _dispatch_provisioning(cp, action):
    """Dispatch a provisioning action by name."""
    dispatch = {
        'get_variables_single': _prov_get_variables_single,
        'get_variables_multiple': _prov_get_variables_multiple,
        'get_variables_split': _prov_get_variables_split,
        'set_variables_single': _prov_set_variables_single,
        'set_variables_multiple': _prov_set_variables_multiple,
        'get_base_report_config': lambda cp: _prov_get_base_report(cp, 'ConfigurationInventory'),
        'get_base_report_full': lambda cp: _prov_get_base_report(cp, 'FullInventory'),
        'get_base_report_summary': lambda cp: _prov_get_base_report(cp, 'SummaryInventory'),
        'get_report_criteria': _prov_get_report_criteria,
        'reset_on_idle_cs': lambda cp: _prov_reset(cp, 'OnIdle', None),
        'reset_immediate_cs': lambda cp: _prov_reset(cp, 'Immediate', None),
        'reset_on_idle_evse': lambda cp: _prov_reset(cp, 'OnIdle', CONFIGURED_EVSE_ID),
        'reset_immediate_evse': lambda cp: _prov_reset(cp, 'Immediate', CONFIGURED_EVSE_ID),
        'trigger_boot': _prov_trigger_boot,
        'set_network_profile': _prov_set_network_profile,
        'send_local_list_full': _prov_send_local_list_full,
        'send_local_list_diff_update': _prov_send_local_list_diff_update,
        'send_local_list_diff_remove': _prov_send_local_list_diff_remove,
        'send_local_list_full_empty': _prov_send_local_list_full_empty,
        'get_local_list_version': _prov_get_local_list_version,
        'change_availability_evse_inoperative': lambda cp: _prov_change_availability(cp, 'Inoperative', 'evse'),
        'change_availability_evse_operative': lambda cp: _prov_change_availability(cp, 'Operative', 'evse'),
        'change_availability_station_inoperative': lambda cp: _prov_change_availability(cp, 'Inoperative', 'station'),
        'change_availability_station_operative': lambda cp: _prov_change_availability(cp, 'Operative', 'station'),
        'change_availability_connector_inoperative': lambda cp: _prov_change_availability(cp, 'Inoperative', 'connector'),
        'change_availability_connector_operative': lambda cp: _prov_change_availability(cp, 'Operative', 'connector'),
    }
    handler = dispatch.get(action)
    if handler:
        await handler(cp)
    else:
        logging.warning(f"Unknown provisioning action: {action}")


async def _prov_get_variables_single(cp):
    logging.info(f"Provisioning: GetVariables(single) for {cp.id}")
    await cp.call(call.GetVariables(get_variable_data=[
        {'component': {'name': 'OCPPCommCtrlr'}, 'variable': {'name': 'OfflineThreshold'}},
    ]))


async def _prov_get_variables_multiple(cp):
    logging.info(f"Provisioning: GetVariables(multiple) for {cp.id}")
    await cp.call(call.GetVariables(get_variable_data=[
        {'component': {'name': 'OCPPCommCtrlr'}, 'variable': {'name': 'OfflineThreshold'}},
        {'component': {'name': 'AuthCtrlr'}, 'variable': {'name': 'AuthorizeRemoteStart'}},
    ]))


async def _prov_get_variables_split(cp):
    logging.info(f"Provisioning: GetVariables(split 4+1) for {cp.id}")
    await cp.call(call.GetVariables(get_variable_data=[
        {'component': {'name': 'DeviceDataCtrlr'}, 'variable': {'name': 'ItemsPerMessage', 'instance': 'GetReport'}},
        {'component': {'name': 'DeviceDataCtrlr'}, 'variable': {'name': 'ItemsPerMessage', 'instance': 'GetVariables'}},
        {'component': {'name': 'DeviceDataCtrlr'}, 'variable': {'name': 'BytesPerMessage', 'instance': 'GetReport'}},
        {'component': {'name': 'DeviceDataCtrlr'}, 'variable': {'name': 'BytesPerMessage', 'instance': 'GetVariables'}},
    ]))
    await asyncio.sleep(0.5)
    await cp.call(call.GetVariables(get_variable_data=[
        {'component': {'name': 'AuthCtrlr'}, 'variable': {'name': 'AuthorizeRemoteStart'}},
    ]))


async def _prov_set_variables_single(cp):
    logging.info(f"Provisioning: SetVariables(single) for {cp.id}")
    await cp.call(call.SetVariables(set_variable_data=[{
        'component': {'name': 'OCPPCommCtrlr'},
        'variable': {'name': 'OfflineThreshold'},
        'attribute_value': '123',
    }]))


async def _prov_set_variables_multiple(cp):
    logging.info(f"Provisioning: SetVariables(multiple) for {cp.id}")
    await cp.call(call.SetVariables(set_variable_data=[
        {
            'component': {'name': 'OCPPCommCtrlr'},
            'variable': {'name': 'OfflineThreshold'},
            'attribute_value': '123',
        },
        {
            'component': {'name': 'AuthCtrlr'},
            'variable': {'name': 'AuthorizeRemoteStart'},
            'attribute_value': 'false',
        },
    ]))


async def _prov_get_base_report(cp, report_base):
    logging.info(f"Provisioning: GetBaseReport({report_base}) for {cp.id}")
    await cp.call(call.GetBaseReport(
        request_id=_next_request_id(),
        report_base=report_base,
    ))


async def _prov_get_report_criteria(cp):
    logging.info(f"Provisioning: GetReport(Problem then Available) for {cp.id}")
    evse_id = CONFIGURED_EVSE_ID
    cv = [{'component': {'name': 'EVSE', 'evse': {'id': evse_id}},
           'variable': {'name': 'AvailabilityState'}}]

    await cp.call(call.GetReport(
        request_id=_next_request_id(),
        component_criteria=['Problem'],
        component_variable=cv,
    ))
    await asyncio.sleep(0.5)
    await cp.call(call.GetReport(
        request_id=_next_request_id(),
        component_criteria=['Available'],
        component_variable=cv,
    ))


async def _prov_reset(cp, reset_type, evse_id):
    logging.info(f"Provisioning: Reset({reset_type}, evse_id={evse_id}) for {cp.id}")
    kwargs = {'type': reset_type}
    if evse_id is not None:
        kwargs['evse_id'] = evse_id
    try:
        await asyncio.wait_for(cp.call(call.Reset(**kwargs)), timeout=10)
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Reset call did not complete for {cp.id}: {e}")


async def _prov_trigger_boot(cp):
    logging.info(f"Provisioning: TriggerMessage(BootNotification) for {cp.id}")
    await cp.call(call.TriggerMessage(requested_message='BootNotification'))


async def _prov_set_network_profile(cp):
    logging.info(f"Provisioning: SetNetworkProfile for {cp.id}")
    await cp.call(call.SetNetworkProfile(
        configuration_slot=CONFIGURED_CONFIGURATION_SLOT,
        connection_data={
            'ocpp_version': 'OCPP20',
            'ocpp_transport': 'JSON',
            'ocpp_csms_url': CONFIGURED_OCPP_CSMS_URL,
            'message_timeout': CONFIGURED_MESSAGE_TIMEOUT_B,
            'security_profile': CONFIGURED_SECURITY_PROFILE,
            'ocpp_interface': CONFIGURED_OCPP_INTERFACE,
        },
    ))


async def _prov_send_local_list_full(cp):
    logging.info(f"Provisioning: SendLocalList(Full) for {cp.id}")
    await cp.call(call.SendLocalList(
        version_number=1,
        update_type='Full',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
            {
                'id_token': {'id_token': 'D001002', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
        ]
    ))


async def _prov_send_local_list_diff_update(cp):
    logging.info(f"Provisioning: SendLocalList(Differential, add) for {cp.id}")
    await cp.call(call.GetLocalListVersion())
    await asyncio.sleep(0.5)
    await cp.call(call.SendLocalList(
        version_number=2,
        update_type='Differential',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
        ]
    ))


async def _prov_send_local_list_diff_remove(cp):
    logging.info(f"Provisioning: SendLocalList(Differential, remove) for {cp.id}")
    await cp.call(call.SendLocalList(
        version_number=3,
        update_type='Differential',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
            },
        ]
    ))


async def _prov_send_local_list_full_empty(cp):
    logging.info(f"Provisioning: SendLocalList(Full, empty) for {cp.id}")
    await cp.call(call.SendLocalList(
        version_number=1,
        update_type='Full',
    ))


async def _prov_get_local_list_version(cp):
    logging.info(f"Provisioning: GetLocalListVersion for {cp.id}")
    await cp.call(call.GetLocalListVersion())


async def _prov_change_availability(cp, op_status, target):
    """Send ChangeAvailabilityRequest with the given status and target level."""
    kwargs = {'operational_status': op_status}
    if target == 'connector':
        kwargs['evse'] = {'id': CONFIGURED_EVSE_ID, 'connector_id': CONFIGURED_CONNECTOR_ID}
    elif target == 'evse':
        kwargs['evse'] = {'id': CONFIGURED_EVSE_ID}
    # station-level: no evse parameter
    logging.info(f"Provisioning: ChangeAvailability({op_status}, {target}) for {cp.id}")
    await cp.call(call.ChangeAvailability(**kwargs))


# ─── E-Mode Actions ──────────────────────────────────────────────────────────

async def _delayed_e_action(cp, action, idx, delay=3):
    """Execute an E-mode action after a delay, unless cancelled by new CP messages."""
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        txn_id = _e_cp_transactions.get(cp.id)
        _e_action_index[cp.id] = idx + 1
        logging.info(f"E-mode delayed action #{idx} for {cp.id}: {action} (txn={txn_id})")
        await _execute_e_action(cp, action, txn_id)
    except asyncio.CancelledError:
        pass  # Cancelled because CP sent another message
    except Exception as e:
        logging.warning(f"E-mode delayed action failed for {cp.id}: {e}")
    finally:
        _e_pending_action_task.pop(cp.id, None)


async def _execute_e_action(cp, action, txn_id=None):
    """Execute an E-mode CSMS-initiated action."""
    if action == 'request_stop_transaction' and txn_id:
        logging.info(f"Sending RequestStopTransaction to {cp.id} (txn={txn_id})")
        await cp.call(call.RequestStopTransaction(transaction_id=txn_id))
    elif action == 'get_transaction_status' and txn_id:
        logging.info(f"Sending GetTransactionStatus to {cp.id} (txn={txn_id})")
        await cp.call(call.GetTransactionStatus(transaction_id=txn_id))
    elif action == 'get_transaction_status_no_id':
        logging.info(f"Sending GetTransactionStatus (no txId) to {cp.id}")
        await cp.call(call.GetTransactionStatus())
    else:
        logging.warning(f"E-mode: unknown action '{action}' or missing txn_id for {cp.id}")


# ─── F-Mode Actions ──────────────────────────────────────────────────────────

async def _delayed_f_action(cp, idx, delay=2):
    """Execute an F-mode action after a delay of silence from the CP."""
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        action = _SP1_F_PROVISIONING[idx]
        global _f_remote_start_id
        _f_action_index[cp.id] = idx + 1
        cp._f_action_fired_for_session = True
        logging.info(f"F-mode action #{idx} for {cp.id}: {action}")
        await _execute_f_action(cp, action)
    except asyncio.CancelledError:
        pass  # Cancelled because CP sent another message
    except Exception as e:
        logging.warning(f"F-mode action failed for {cp.id}: {e}")
    finally:
        _f_pending_action_task.pop(cp.id, None)


async def _execute_f_action(cp, action):
    """Execute an F-mode CSMS-initiated action."""
    if action == 'request_start_transaction':
        await _f_request_start_transaction(cp)
    elif action == 'unlock_connector':
        await _f_unlock_connector(cp)
    elif action.startswith('trigger_'):
        trigger_map = {
            'trigger_meter_values_evse': ('MeterValues', {'id': CONFIGURED_EVSE_ID}),
            'trigger_meter_values_all': ('MeterValues', None),
            'trigger_transaction_event_evse': ('TransactionEvent', {'id': CONFIGURED_EVSE_ID}),
            'trigger_transaction_event_all': ('TransactionEvent', None),
            'trigger_log_status': ('LogStatusNotification', None),
            'trigger_firmware_status': ('FirmwareStatusNotification', None),
            'trigger_heartbeat': ('Heartbeat', None),
            'trigger_status_notification_evse': ('StatusNotification', {'id': CONFIGURED_EVSE_ID}),
        }
        msg_type, evse = trigger_map.get(action, (None, None))
        if msg_type:
            await _f_trigger_message(cp, msg_type, evse)
        else:
            logging.warning(f"F-mode: unknown trigger action '{action}' for {cp.id}")
    else:
        logging.warning(f"F-mode: unknown action '{action}' for {cp.id}")


async def _f_request_start_transaction(cp):
    global _f_remote_start_id
    _f_remote_start_id += 1
    logging.info(f"Sending RequestStartTransaction to {cp.id} "
                 f"(remote_start_id={_f_remote_start_id})")
    await cp.call(call.RequestStartTransaction(
        id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
        remote_start_id=_f_remote_start_id,
    ))


async def _f_unlock_connector(cp):
    logging.info(f"Sending UnlockConnector to {cp.id} "
                 f"(evse_id={CONFIGURED_EVSE_ID}, connector_id={CONFIGURED_CONNECTOR_ID})")
    await cp.call(call.UnlockConnector(
        evse_id=CONFIGURED_EVSE_ID,
        connector_id=CONFIGURED_CONNECTOR_ID,
    ))


async def _f_trigger_message(cp, requested_message, evse=None):
    logging.info(f"Sending TriggerMessage({requested_message}, evse={evse}) to {cp.id}")
    kwargs = {'requested_message': requested_message}
    if evse is not None:
        kwargs['evse'] = evse
    await cp.call(call.TriggerMessage(**kwargs))


# ─── Post-Provisioning Actions ────────────────────────────────────────────────

async def _delayed_post_prov_action(cp, delay=2):
    """Execute a post-provisioning action after a delay of silence from the CP."""
    global _post_prov_global_index
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        idx = _post_prov_global_index
        if idx >= len(_POST_PROVISIONING_ACTIONS):
            return
        action = _POST_PROVISIONING_ACTIONS[idx]
        if action is None:
            return
        _post_prov_global_index = idx + 1
        cp._post_prov_action_fired_for_session = True
        # Remove from pending dict before executing to prevent route_message
        # from cancelling this task mid-execution (cp.call responses go through
        # route_message which would cancel the still-running task).
        if _post_prov_pending_task.get(cp.id) is this_task:
            del _post_prov_pending_task[cp.id]
        logging.info(f"Post-provisioning action #{idx} for {cp.id}: {action}")
        await _dispatch_provisioning(cp, action)
    except asyncio.CancelledError:
        pass  # Cancelled because CP sent another message
    except Exception as e:
        logging.warning(f"Post-provisioning action failed for {cp.id}: {e}")
    finally:
        # Only clean up if we're still the registered task (prevents race
        # where a new session's task gets removed by a finishing old task).
        if _post_prov_pending_task.get(cp.id) is this_task:
            del _post_prov_pending_task[cp.id]


# ─── H-Mode Actions ──────────────────────────────────────────────────────────

def _next_h_reservation_id():
    global _h_reservation_id
    _h_reservation_id += 1
    return _h_reservation_id


def _h_expiry_iso(seconds):
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(1, seconds))
    return expires_at.replace(microsecond=0).isoformat().replace('+00:00', 'Z')


async def _h_send_reserve_now(cp, *, evse_id=None, connector_type=None,
                              include_group=False, expiry_seconds=TRANSACTION_DURATION):
    reservation_id = _next_h_reservation_id()
    kwargs = {
        'id': reservation_id,
        'expiry_date_time': _h_expiry_iso(expiry_seconds),
        'id_token': {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    }
    if evse_id is not None:
        kwargs['evse_id'] = evse_id
    if connector_type is not None:
        kwargs['connector_type'] = connector_type
    if include_group:
        kwargs['group_id_token'] = {'id_token': VALID_TOKEN_GROUP, 'type': 'Central'}

    logging.info(
        f"H-mode: sending ReserveNow to {cp.id} "
        f"(reservation_id={reservation_id}, evse_id={kwargs.get('evse_id')}, "
        f"connector_type={kwargs.get('connector_type')}, include_group={include_group})"
    )
    response = await cp.call(call.ReserveNow(**kwargs))
    logging.info(f"H-mode: ReserveNowResponse from {cp.id}: {response}")
    return reservation_id


async def _execute_h_action(cp, action):
    if action == 'reserve_specific':
        await _h_send_reserve_now(cp, evse_id=CONFIGURED_EVSE_ID)
    elif action == 'reserve_specific_expiry':
        await _h_send_reserve_now(
            cp,
            evse_id=CONFIGURED_EVSE_ID,
            expiry_seconds=TRANSACTION_DURATION,
        )
    elif action == 'reserve_unspecified':
        await _h_send_reserve_now(cp)
    elif action == 'reserve_unspecified_multi':
        reservations_to_send = max(1, CONFIGURED_NUMBER_OF_EVSES)
        for i in range(reservations_to_send):
            await _h_send_reserve_now(cp)
            # Give the test harness time to consume each request individually.
            if i < reservations_to_send - 1:
                await asyncio.sleep(1)
    elif action == 'reserve_connector_type':
        await _h_send_reserve_now(cp, connector_type=CONFIGURED_CONNECTOR_TYPE)
    elif action == 'reserve_then_cancel':
        reservation_id = await _h_send_reserve_now(cp, evse_id=CONFIGURED_EVSE_ID)
        await asyncio.sleep(1)
        logging.info(
            f"H-mode: sending CancelReservation to {cp.id} "
            f"(reservation_id={reservation_id})"
        )
        response = await cp.call(call.CancelReservation(reservation_id=reservation_id))
        logging.info(f"H-mode: CancelReservationResponse from {cp.id}: {response}")
    elif action == 'reserve_specific_group':
        await _h_send_reserve_now(
            cp,
            evse_id=CONFIGURED_EVSE_ID,
            include_group=True,
        )
    else:
        logging.warning(f"H-mode: unknown action '{action}' for {cp.id}")


async def _delayed_h_action(cp, idx, delay=2):
    """Execute an H-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        action = _SP1_H_PROVISIONING[idx]
        cp._h_action_fired_for_session = True
        # Remove before cp.call() so route_message doesn't cancel us with call results.
        if _h_pending_action_task.get(cp.id) is this_task:
            del _h_pending_action_task[cp.id]
        logging.info(f"H-mode action #{idx} for {cp.id}: {action}")
        await _execute_h_action(cp, action)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"H-mode action failed for {cp.id}: {e}")
    finally:
        if _h_pending_action_task.get(cp.id) is this_task:
            del _h_pending_action_task[cp.id]


# ─── K-Mode Actions ──────────────────────────────────────────────────────────

async def _execute_k_action(cp, action):
    if action == 'set_tx_default_specific':
        profile = _k_profile(
            _k_next_profile_id(),
            'TxDefaultProfile',
            'Absolute',
            6.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile)

    elif action == 'set_tx_profile_no_tx':
        profile = _k_profile(
            _k_next_profile_id(),
            'TxProfile',
            'Relative',
            7.0,
            include_start_schedule=False,
            include_valid_window=False,
        )
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile)

    elif action == 'set_station_max_profile':
        profile = _k_profile(
            _k_next_profile_id(),
            'ChargingStationMaxProfile',
            'Absolute',
            8.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        await _k_send_set_charging_profile(cp, 0, profile)

    elif action == 'set_replace_same_id':
        replace_id = getattr(cp, '_k_replace_profile_id', None)
        if replace_id is None:
            replace_id = _k_next_profile_id()
            cp._k_replace_profile_id = replace_id
        profile_a = _k_profile(
            replace_id,
            'TxDefaultProfile',
            'Absolute',
            8.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        profile_b = _k_profile(
            replace_id,
            'TxDefaultProfile',
            'Absolute',
            6.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile_a)
        await asyncio.sleep(0.5)
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile_b)

    elif action == 'get_then_clear_by_id':
        cp._k_pending_clear_from_report = True
        await _k_send_get_charging_profiles(
            cp,
            {'charging_profile_purpose': 'TxDefaultProfile'},
            evse_id=CONFIGURED_EVSE_ID,
        )

    elif action == 'clear_by_criteria':
        await _k_send_clear_charging_profile(
            cp,
            criteria={
                'charging_profile_purpose': 'TxDefaultProfile',
                'stack_level': CONFIGURED_STACK_LEVEL,
                'evse_id': CONFIGURED_EVSE_ID,
            },
        )

    elif action == 'set_tx_default_all':
        profile = _k_profile(
            _k_next_profile_id(),
            'TxDefaultProfile',
            'Absolute',
            6.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        await _k_send_set_charging_profile(cp, 0, profile)

    elif action == 'set_tx_default_recurring':
        profile = _k_profile(
            _k_next_profile_id(),
            'TxDefaultProfile',
            'Recurring',
            6.0,
            include_start_schedule=True,
            include_valid_window=True,
            recurrency_kind='Daily',
        )
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile)

    elif action == 'get_profiles_evse0_purpose':
        await _k_send_get_charging_profiles(
            cp,
            {'charging_profile_purpose': 'TxDefaultProfile'},
            evse_id=0,
        )

    elif action == 'get_profiles_evse_purpose':
        await _k_send_get_charging_profiles(
            cp,
            {'charging_profile_purpose': 'TxDefaultProfile'},
            evse_id=CONFIGURED_EVSE_ID,
        )

    elif action == 'get_profiles_no_evse_purpose':
        await _k_send_get_charging_profiles(
            cp,
            {'charging_profile_purpose': 'TxDefaultProfile'},
            evse_id=None,
        )

    elif action == 'get_profiles_by_id':
        await _k_send_get_charging_profiles(
            cp,
            {'charging_profile_id': [100]},
            evse_id=None,
        )

    elif action == 'get_profiles_evse_stack':
        await _k_send_get_charging_profiles(
            cp,
            {'stack_level': CONFIGURED_STACK_LEVEL},
            evse_id=CONFIGURED_EVSE_ID,
        )

    elif action == 'get_profiles_evse_source':
        ok = await _k_send_get_charging_profiles(
            cp,
            {'charging_limit_source': ['CSO']},
            evse_id=CONFIGURED_EVSE_ID,
        )
        if not ok:
            # Compatibility fallback for stacks that expect a scalar value.
            await asyncio.sleep(0.2)
            await _k_send_get_charging_profiles(
                cp,
                {'charging_limit_source': 'CSO'},
                evse_id=CONFIGURED_EVSE_ID,
            )

    elif action == 'get_profiles_evse_purpose_stack':
        await _k_send_get_charging_profiles(
            cp,
            {
                'charging_profile_purpose': 'TxDefaultProfile',
                'stack_level': CONFIGURED_STACK_LEVEL,
            },
            evse_id=CONFIGURED_EVSE_ID,
        )

    elif action == 'request_start_tx_with_profile':
        profile = _k_profile(
            _k_next_profile_id(),
            'TxProfile',
            'Relative',
            7.0,
            include_start_schedule=False,
            include_valid_window=False,
            transaction_id=None,
        )
        remote_start_id = _k_next_request_start_id()
        logging.info(
            f"K-mode: sending RequestStartTransaction to {cp.id} "
            f"(remote_start_id={remote_start_id})"
        )
        try:
            await cp.call(call.RequestStartTransaction(
                id_token={'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
                remote_start_id=remote_start_id,
                evse_id=CONFIGURED_EVSE_ID,
                charging_profile=profile,
            ))
        except Exception as e:
            logging.warning(f"K-mode RequestStartTransaction failed for {cp.id}: {e}")

    elif action == 'get_composite_evse':
        await _k_send_get_composite_schedule(cp, evse_id=CONFIGURED_EVSE_ID)

    elif action == 'get_composite_station':
        await _k_send_get_composite_schedule(cp, evse_id=0)

    elif action is None:
        logging.info(f"K-mode: no proactive action for {cp.id} (session_index={_k_session_index(cp)})")

    else:
        logging.warning(f"K-mode: unknown action '{action}' for {cp.id}")


async def _delayed_k_action(cp, idx, delay=2):
    """Execute a K-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if not (0 <= idx < len(_SP1_K_PROVISIONING)):
            return
        action = _SP1_K_PROVISIONING[idx]
        cp._k_action_fired_for_session = True
        if _k_pending_action_task.get(cp.id) is this_task:
            del _k_pending_action_task[cp.id]
        logging.info(f"K-mode action #{idx} for {cp.id}: {action}")
        await _execute_k_action(cp, action)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"K-mode action failed for {cp.id}: {e}")
    finally:
        if _k_pending_action_task.get(cp.id) is this_task:
            del _k_pending_action_task[cp.id]


async def _execute_l_action(cp, plan):
    op = plan.get('op')
    variant = plan.get('variant', 'standard')
    cp._l_flow_state = {
        'op': op,
        'variant': variant,
        'request_id': None,
        'second_update_pending': variant == 'replace_on_downloading',
        'second_update_sent': False,
    }

    if op == 'update':
        update_variant = variant if variant in ('install_scheduled', 'download_scheduled') else 'secure'
        req_id = await _l_send_update_firmware(cp, variant=update_variant, alternate=False)
        cp._l_flow_state['request_id'] = req_id
        return

    if op == 'publish':
        req_id = await _l_send_publish_firmware(cp)
        cp._l_flow_state['request_id'] = req_id
        return

    if op == 'unpublish':
        await _l_send_unpublish_firmware(cp)
        return

    logging.warning(f"L-mode: unknown action plan {plan!r} for {cp.id}")


async def _l_handle_firmware_status(cp, *, status_text, request_id=None):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    state = cp._l_flow_state or {}
    if not state.get('second_update_pending'):
        return
    if state.get('second_update_sent'):
        return
    if status_text != 'Downloading':
        return

    state['second_update_sent'] = True
    cp._l_flow_state = state
    await asyncio.sleep(0.1)
    logging.info(
        f"L-mode: {cp.id} reported Downloading during replace flow; "
        f"sending follow-up UpdateFirmware"
    )
    await _l_send_update_firmware(cp, variant='secure', alternate=True)


async def _delayed_l_action(cp, idx, delay=2):
    """Execute an L-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if not (0 <= idx < len(_SP1_L_PROVISIONING)):
            return
        plan = _SP1_L_PROVISIONING[idx]
        cp._l_action_fired_for_session = True
        if _l_pending_action_task.get(cp.id) is this_task:
            del _l_pending_action_task[cp.id]
        logging.info(f"L-mode action #{idx} for {cp.id}: {plan}")
        await _execute_l_action(cp, plan)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"L-mode action failed for {cp.id}: {e}")
    finally:
        if _l_pending_action_task.get(cp.id) is this_task:
            del _l_pending_action_task[cp.id]


def _m_get_field(obj, *names):
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        return None
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _m_normalize_hash_data(hash_data):
    if hash_data is None:
        return None
    normalized = {
        'hash_algorithm': _m_get_field(hash_data, 'hash_algorithm', 'hashAlgorithm'),
        'issuer_name_hash': _m_get_field(hash_data, 'issuer_name_hash', 'issuerNameHash'),
        'issuer_key_hash': _m_get_field(hash_data, 'issuer_key_hash', 'issuerKeyHash'),
        'serial_number': _m_get_field(hash_data, 'serial_number', 'serialNumber'),
    }
    if any(v is None for v in normalized.values()):
        return None
    return normalized


def _m_extract_hash_data_from_response(response, certificate_types=None):
    chain = _m_get_field(response, 'certificate_hash_data_chain', 'certificateHashDataChain')
    if chain is None:
        return None
    if not isinstance(chain, list):
        chain = [chain]

    expected_types = None
    if certificate_types is not None:
        expected_types = {_enum_text(x) for x in certificate_types}

    fallback = None
    for entry in chain:
        cert_type = _m_get_field(entry, 'certificate_type', 'certificateType')
        hash_data = _m_get_field(entry, 'certificate_hash_data', 'certificateHashData')
        normalized = _m_normalize_hash_data(hash_data)
        if normalized is None:
            continue
        if fallback is None:
            fallback = normalized
        if expected_types is None or _enum_text(cert_type) in expected_types:
            return normalized
    return fallback


async def _m_send_install_certificate(cp, install_type):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    logging.info(
        f"M-mode: sending InstallCertificate to {cp.id} "
        f"(certificate_type={install_type})"
    )
    try:
        response = await cp.call(call.InstallCertificate(
            certificate_type=install_type,
            certificate=_M_CERTIFICATE_PEM,
        ))
        logging.info(f"M-mode: InstallCertificateResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"M-mode InstallCertificate failed for {cp.id}: {e}")
        return None


async def _m_send_get_installed_certificate_ids(cp, certificate_types):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    kwargs = {}
    if certificate_types is not None:
        if not isinstance(certificate_types, list):
            certificate_types = [certificate_types]
        kwargs['certificate_type'] = certificate_types
    logging.info(
        f"M-mode: sending GetInstalledCertificateIds to {cp.id} "
        f"(certificate_type={kwargs.get('certificate_type')})"
    )
    try:
        response = await cp.call(call.GetInstalledCertificateIds(**kwargs))
        logging.info(f"M-mode: GetInstalledCertificateIdsResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"M-mode GetInstalledCertificateIds failed for {cp.id}: {e}")
        return None


async def _m_send_delete_certificate(cp, certificate_hash_data):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    if not certificate_hash_data:
        logging.warning(f"M-mode: no certificate_hash_data available for DeleteCertificate to {cp.id}")
        return None
    logging.info(
        f"M-mode: sending DeleteCertificate to {cp.id} "
        f"(hash_algorithm={certificate_hash_data.get('hash_algorithm')})"
    )
    try:
        response = await cp.call(call.DeleteCertificate(
            certificate_hash_data=certificate_hash_data
        ))
        logging.info(f"M-mode: DeleteCertificateResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"M-mode DeleteCertificate failed for {cp.id}: {e}")
        return None


async def _execute_m_action(cp, plan):
    if plan is None:
        logging.info(f"M-mode: no proactive action for {cp.id} (session_index={_m_session_index(cp)})")
        return

    op = plan.get('op')
    if op == 'install_certificate':
        await _m_send_install_certificate(cp, plan['install_type'])
        return

    if op == 'get_installed_ids':
        certificate_types = plan.get('certificate_type')
        repeat = max(1, int(plan.get('repeat', 1)))
        for i in range(repeat):
            response = await _m_send_get_installed_certificate_ids(cp, certificate_types)
            hash_data = _m_extract_hash_data_from_response(response, certificate_types)
            if hash_data is not None:
                cp._m_last_certificate_hash_data = hash_data
                _m_last_cert_hash_data[cp.id] = hash_data
            if i < repeat - 1:
                # Keep a short gap so test harness can reconfigure next response.
                await asyncio.sleep(1.0)
        return

    if op == 'install_get_delete':
        install_type = plan.get('install_type', InstallCertificateUseEnumType.csms_root_certificate)
        certificate_types = plan.get('certificate_type')
        await _m_send_install_certificate(cp, install_type)
        await asyncio.sleep(0.3)
        response = await _m_send_get_installed_certificate_ids(cp, certificate_types)
        hash_data = _m_extract_hash_data_from_response(response, certificate_types)
        if hash_data is not None:
            cp._m_last_certificate_hash_data = hash_data
            _m_last_cert_hash_data[cp.id] = hash_data
        else:
            hash_data = cp._m_last_certificate_hash_data or _m_last_cert_hash_data.get(cp.id)
        await asyncio.sleep(0.3)
        await _m_send_delete_certificate(cp, hash_data)
        return

    logging.warning(f"M-mode: unknown action plan {plan!r} for {cp.id}")


async def _delayed_m_action(cp, idx, delay=2):
    """Execute an M-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if not (0 <= idx < len(_SP1_M_PROVISIONING)):
            return
        plan = _SP1_M_PROVISIONING[idx]
        cp._m_action_fired_for_session = True
        if _m_pending_action_task.get(cp.id) is this_task:
            del _m_pending_action_task[cp.id]
        logging.info(f"M-mode action #{idx} for {cp.id}: {plan}")
        await _execute_m_action(cp, plan)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"M-mode action failed for {cp.id}: {e}")
    finally:
        if _m_pending_action_task.get(cp.id) is this_task:
            del _m_pending_action_task[cp.id]


def _n_get_field(obj, *names):
    return _m_get_field(obj, *names)


def _n_extract_items_per_message(response, default_value=3):
    results = _n_get_field(response, 'get_variable_result', 'getVariableResult') or []
    if not isinstance(results, list):
        results = [results]
    for item in results:
        component = _n_get_field(item, 'component')
        variable = _n_get_field(item, 'variable')
        if _n_get_field(component, 'name') != 'MonitoringCtrlr':
            continue
        if _n_get_field(variable, 'name') != 'ItemsPerMessage':
            continue
        instance = _n_get_field(variable, 'instance')
        if instance not in (None, 'ClearVariableMonitoring'):
            continue
        raw_value = _n_get_field(item, 'attribute_value', 'attributeValue')
        try:
            parsed = int(str(raw_value))
            return max(1, parsed)
        except (TypeError, ValueError):
            break
    return max(1, int(default_value))


def _n_chunk_ids(ids, chunk_size):
    size = max(1, int(chunk_size))
    return [ids[i:i + size] for i in range(0, len(ids), size)]


async def _n_send_get_monitoring_report(cp, *, monitoring_criteria=None, component_variable=None):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    request_id = _next_request_id()
    kwargs = {'request_id': request_id}
    if monitoring_criteria is not None:
        kwargs['monitoring_criteria'] = deepcopy(monitoring_criteria)
    if component_variable is not None:
        kwargs['component_variable'] = deepcopy(component_variable)
    logging.info(
        f"N-mode: sending GetMonitoringReport to {cp.id} "
        f"(request_id={request_id}, criteria={kwargs.get('monitoring_criteria')}, "
        f"component_variable={kwargs.get('component_variable')})"
    )
    try:
        response = await cp.call(call.GetMonitoringReport(**kwargs))
        logging.info(f"N-mode: GetMonitoringReportResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode GetMonitoringReport failed for {cp.id}: {e}")
        return None


async def _n_send_set_monitoring_base(cp, monitoring_base):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    logging.info(
        f"N-mode: sending SetMonitoringBase to {cp.id} "
        f"(monitoring_base={monitoring_base})"
    )
    try:
        response = await cp.call(call.SetMonitoringBase(monitoring_base=monitoring_base))
        logging.info(f"N-mode: SetMonitoringBaseResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode SetMonitoringBase failed for {cp.id}: {e}")
        return None


async def _n_send_set_variable_monitoring(cp, set_monitoring_data):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    payload = deepcopy(set_monitoring_data)
    logging.info(
        f"N-mode: sending SetVariableMonitoring to {cp.id} "
        f"(items={len(payload)})"
    )
    try:
        response = await cp.call(call.SetVariableMonitoring(set_monitoring_data=payload))
        logging.info(f"N-mode: SetVariableMonitoringResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode SetVariableMonitoring failed for {cp.id}: {e}")
        return None


async def _n_send_set_monitoring_level(cp, severity):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    logging.info(f"N-mode: sending SetMonitoringLevel to {cp.id} (severity={severity})")
    try:
        response = await cp.call(call.SetMonitoringLevel(severity=int(severity)))
        logging.info(f"N-mode: SetMonitoringLevelResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode SetMonitoringLevel failed for {cp.id}: {e}")
        return None


async def _n_send_get_variables_items_per_message(cp):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    get_variable_data = [{
        'component': {'name': 'MonitoringCtrlr'},
        'variable': {'name': 'ItemsPerMessage', 'instance': 'ClearVariableMonitoring'},
    }]
    logging.info(f"N-mode: sending GetVariables(ItemsPerMessage/ClearVariableMonitoring) to {cp.id}")
    try:
        response = await cp.call(call.GetVariables(get_variable_data=get_variable_data))
        logging.info(f"N-mode: GetVariablesResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode GetVariables failed for {cp.id}: {e}")
        return None


async def _n_send_clear_variable_monitoring(cp, ids):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    id_list = [int(x) for x in ids]
    logging.info(
        f"N-mode: sending ClearVariableMonitoring to {cp.id} "
        f"(ids={id_list})"
    )
    try:
        response = await cp.call(call.ClearVariableMonitoring(id=id_list))
        logging.info(f"N-mode: ClearVariableMonitoringResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode ClearVariableMonitoring failed for {cp.id}: {e}")
        return None


async def _n_send_get_log(cp, *, log_type, request_id=None):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    if request_id is None:
        request_id = _next_request_id()
    logging.info(
        f"N-mode: sending GetLog to {cp.id} "
        f"(request_id={request_id}, log_type={log_type})"
    )
    try:
        response = await cp.call(call.GetLog(
            log={'remote_location': _N_LOG_REMOTE_LOCATION},
            log_type=log_type,
            request_id=request_id,
            retries=1,
            retry_interval=5,
        ))
        logging.info(f"N-mode: GetLogResponse from {cp.id}: {response}")
        return request_id
    except Exception as e:
        logging.warning(f"N-mode GetLog failed for {cp.id}: {e}")
        return None


async def _n_send_customer_information(cp, *, report, clear, ref, request_id=None):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    if request_id is None:
        request_id = _next_request_id()
    kwargs = {
        'request_id': request_id,
        'report': bool(report),
        'clear': bool(clear),
    }
    if ref == 'id_token':
        kwargs['id_token'] = {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE}
    elif ref == 'customer_identifier':
        kwargs['customer_identifier'] = 'OpenChargeAlliance'
    elif ref == 'customer_certificate':
        kwargs['customer_certificate'] = deepcopy(_N_CUSTOMER_CERTIFICATE_HASH)
    logging.info(
        f"N-mode: sending CustomerInformation to {cp.id} "
        f"(request_id={request_id}, report={report}, clear={clear}, ref={ref})"
    )
    try:
        response = await cp.call(call.CustomerInformation(**kwargs))
        logging.info(f"N-mode: CustomerInformationResponse from {cp.id}: {response}")
        return request_id
    except Exception as e:
        logging.warning(f"N-mode CustomerInformation failed for {cp.id}: {e}")
        return None


async def _n_send_send_local_list_differential(cp):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    version_number = max(1, LOCAL_LIST_VERSION) + 1
    payload = [{
        'id_token': {'id_token': VALID_ID_TOKEN, 'type': VALID_ID_TOKEN_TYPE},
    }]
    logging.info(
        f"N-mode: sending SendLocalList(Differential) to {cp.id} "
        f"(version_number={version_number})"
    )
    try:
        response = await cp.call(call.SendLocalList(
            version_number=version_number,
            update_type='Differential',
            local_authorization_list=payload,
        ))
        logging.info(f"N-mode: SendLocalListResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"N-mode SendLocalList failed for {cp.id}: {e}")
        return None


async def _n_execute_monitoring_report_pair(cp, first, second):
    await _n_send_get_monitoring_report(
        cp,
        monitoring_criteria=first.get('monitoring_criteria'),
        component_variable=first.get('component_variable'),
    )
    await asyncio.sleep(0.5)
    await _n_send_get_monitoring_report(
        cp,
        monitoring_criteria=second.get('monitoring_criteria'),
        component_variable=second.get('component_variable'),
    )


async def _n_handle_log_status(cp, *, status_text, request_id):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    state = cp._n_flow_state or {}
    if state.get('op') != 'get_log_dual':
        return
    if state.get('second_sent'):
        return
    first_request_id = state.get('first_request_id')
    if first_request_id is None or request_id is None:
        return
    if status_text != 'Uploading':
        return
    if str(request_id) != str(first_request_id):
        return
    state['second_sent'] = True
    cp._n_flow_state = state
    await asyncio.sleep(0.2)
    second_request_id = await _n_send_get_log(cp, log_type=state.get('log_type', LogEnumType.diagnostics_log))
    state['second_request_id'] = second_request_id
    cp._n_flow_state = state


async def _n_handle_notify_customer_information(cp, *, request_id):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    state = cp._n_flow_state or {}
    if state.get('op') != 'customer_info_local_list_pending':
        return
    if state.get('local_list_sent'):
        return
    expected_request_id = state.get('customer_request_id')
    if expected_request_id is not None and str(request_id) != str(expected_request_id):
        return
    state['local_list_sent'] = True
    cp._n_flow_state = state
    await asyncio.sleep(0.2)
    await _n_send_send_local_list_differential(cp)


async def _execute_n_action(cp, plan):
    cp._n_flow_state = None
    if plan is None:
        logging.info(f"N-mode: no proactive action for {cp.id} (session_index={_n_session_index(cp)})")
        return

    op = plan.get('op')
    if op == 'get_monitoring_report_pair':
        await _n_execute_monitoring_report_pair(cp, plan['first'], plan['second'])
        return

    if op == 'get_monitoring_report':
        await _n_send_get_monitoring_report(
            cp,
            monitoring_criteria=plan.get('monitoring_criteria'),
            component_variable=plan.get('component_variable'),
        )
        return

    if op == 'set_monitoring_base_sequence':
        bases = plan.get('bases', [])
        for i, base in enumerate(bases):
            await _n_send_set_monitoring_base(cp, base)
            if i < len(bases) - 1:
                await asyncio.sleep(0.5)
        return

    if op == 'set_variable_monitoring':
        await _n_send_set_variable_monitoring(cp, plan.get('data', []))
        return

    if op == 'set_monitoring_level':
        await _n_send_set_monitoring_level(cp, plan.get('severity', 4))
        return

    if op == 'clear_variable_monitoring_chunked':
        response = await _n_send_get_variables_items_per_message(cp)
        items_per_message = _n_extract_items_per_message(response, default_value=3)
        ids = plan.get('ids', [1, 2, 3, 4, 5])
        for i, chunk in enumerate(_n_chunk_ids(ids, items_per_message)):
            await _n_send_clear_variable_monitoring(cp, chunk)
            if i < len(_n_chunk_ids(ids, items_per_message)) - 1:
                await asyncio.sleep(0.4)
        return

    if op == 'clear_variable_monitoring':
        await _n_send_clear_variable_monitoring(cp, plan.get('ids', [1]))
        return

    if op == 'get_log':
        await _n_send_get_log(cp, log_type=plan.get('log_type', LogEnumType.diagnostics_log))
        return

    if op == 'get_log_dual':
        first_request_id = _next_request_id()
        cp._n_flow_state = {
            'op': 'get_log_dual',
            'first_request_id': first_request_id,
            'second_sent': False,
            'log_type': plan.get('log_type', LogEnumType.diagnostics_log),
        }
        sent_request_id = await _n_send_get_log(
            cp,
            log_type=plan.get('log_type', LogEnumType.diagnostics_log),
            request_id=first_request_id,
        )
        if sent_request_id is None:
            cp._n_flow_state = None
        return

    if op == 'customer_information':
        if plan.get('send_local_list_on_notify'):
            customer_request_id = _next_request_id()
            cp._n_flow_state = {
                'op': 'customer_info_local_list_pending',
                'customer_request_id': customer_request_id,
                'local_list_sent': False,
            }
            sent_request_id = await _n_send_customer_information(
                cp,
                report=plan.get('report', True),
                clear=plan.get('clear', False),
                ref=plan.get('ref', 'id_token'),
                request_id=customer_request_id,
            )
            if sent_request_id is None:
                cp._n_flow_state = None
            return
        await _n_send_customer_information(
            cp,
            report=plan.get('report', True),
            clear=plan.get('clear', False),
            ref=plan.get('ref', 'id_token'),
        )
        return

    logging.warning(f"N-mode: unknown action plan {plan!r} for {cp.id}")


async def _delayed_n_action(cp, idx, delay=2):
    """Execute an N-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if not (0 <= idx < len(_SP1_N_PROVISIONING)):
            return
        plan = _SP1_N_PROVISIONING[idx]
        cp._n_action_fired_for_session = True
        if _n_pending_action_task.get(cp.id) is this_task:
            del _n_pending_action_task[cp.id]
        logging.info(f"N-mode action #{idx} for {cp.id}: {plan}")
        await _execute_n_action(cp, plan)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"N-mode action failed for {cp.id}: {e}")
    finally:
        if _n_pending_action_task.get(cp.id) is this_task:
            del _n_pending_action_task[cp.id]


def _o_next_message_id():
    global _o_message_id
    _o_message_id += 1
    return _o_message_id


def _o_future_iso(offset_seconds):
    return (
        datetime.now(timezone.utc) + timedelta(seconds=max(1, int(offset_seconds)))
    ).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _o_unknown_message_id(cp, baseline_id=None):
    if baseline_id is None and cp._o_last_display_message:
        baseline_id = cp._o_last_display_message.get('id')
    if baseline_id is not None:
        return int(baseline_id) + 999
    return _o_next_message_id()


def _o_resolve_transaction_id(cp, config, *, observed_transaction_id=None):
    tx_ref = (config or {}).get('transaction_ref')
    if tx_ref is None:
        return None, False
    active_txn = observed_transaction_id or _k_latest_transaction_id.get(cp.id)
    if active_txn is None:
        return None, True
    active_txn = str(active_txn)
    if tx_ref == 'unknown':
        if len(active_txn) <= 1:
            return f"{active_txn}1", False
        last_char = active_txn[-1]
        replacement = '0' if last_char != '0' else '1'
        return f"{active_txn[:-1]}{replacement}", False
    return active_txn, False


def _o_build_set_message(config, *, forced_message_id=None, transaction_id=None):
    config = config or {}
    message_id = forced_message_id if forced_message_id is not None else config.get('message_id')
    if message_id is None:
        message_id = _o_next_message_id()
    include_state = config.get('include_state', True)
    state_value = config.get('state', MessageStateEnumType.idle)
    priority_value = config.get('priority', MessagePriorityEnumType.normal_cycle)
    format_value = config.get('format', MessageFormatEnumType.utf8)
    content_value = config.get('content', f"O-mode message {message_id}")
    include_start = config.get('include_start', config.get('start_date_time') is not None or config.get('start_offset_s') is not None)
    include_end = config.get('include_end', config.get('end_date_time') is not None or config.get('end_offset_s') is not None)
    start_date_time = config.get('start_date_time')
    end_date_time = config.get('end_date_time')
    if include_start and start_date_time is None:
        start_date_time = _o_future_iso(config.get('start_offset_s', 60))
    if include_end and end_date_time is None:
        end_date_time = _o_future_iso(config.get('end_offset_s', 120))

    message = {
        'id': int(message_id),
        'priority': priority_value,
        'message': {
            'format': format_value,
            'content': content_value,
        },
    }
    if include_state:
        message['state'] = state_value
    if include_start:
        message['start_date_time'] = start_date_time
    if include_end:
        message['end_date_time'] = end_date_time
    if transaction_id is not None:
        message['transaction_id'] = str(transaction_id)
    return message


async def _o_send_set_display_message(cp, message):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    logging.info(
        f"O-mode: sending SetDisplayMessage to {cp.id} "
        f"(id={message.get('id')}, priority={message.get('priority')}, "
        f"state={message.get('state')}, transaction_id={message.get('transaction_id')})"
    )
    try:
        response = await cp.call(call.SetDisplayMessage(message=message))
        cp._o_last_display_message = deepcopy(message)
        cp._o_display_messages[int(message['id'])] = deepcopy(message)
        logging.info(f"O-mode: SetDisplayMessageResponse from {cp.id}: {response}")
        return message
    except Exception as e:
        logging.warning(f"O-mode SetDisplayMessage failed for {cp.id}: {e}")
        return None


async def _o_send_set_from_config(cp, config, *, observed_transaction_id=None, forced_message_id=None):
    transaction_id, pending_transaction = _o_resolve_transaction_id(
        cp,
        config,
        observed_transaction_id=observed_transaction_id,
    )
    if pending_transaction:
        return None, True
    message = _o_build_set_message(
        config,
        forced_message_id=forced_message_id,
        transaction_id=transaction_id,
    )
    sent = await _o_send_set_display_message(cp, message)
    return sent, False


async def _o_send_get_display_messages(cp, *, ids=None, priority=None, state=None):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    request_id = _next_request_id()
    kwargs = {'request_id': request_id}
    if ids is not None:
        kwargs['id'] = [int(x) for x in ids]
    if priority is not None:
        kwargs['priority'] = priority
    if state is not None:
        kwargs['state'] = state
    logging.info(
        f"O-mode: sending GetDisplayMessages to {cp.id} "
        f"(request_id={request_id}, id={kwargs.get('id')}, "
        f"priority={kwargs.get('priority')}, state={kwargs.get('state')})"
    )
    try:
        response = await cp.call(call.GetDisplayMessages(**kwargs))
        logging.info(f"O-mode: GetDisplayMessagesResponse from {cp.id}: {response}")
        return request_id
    except Exception as e:
        logging.warning(f"O-mode GetDisplayMessages failed for {cp.id}: {e}")
        return None


async def _o_send_clear_display_message(cp, message_id):
    if _active_cp_instance.get(cp.id) is not cp:
        return None
    message_id = int(message_id)
    logging.info(f"O-mode: sending ClearDisplayMessage to {cp.id} (id={message_id})")
    try:
        response = await cp.call(call.ClearDisplayMessage(id=message_id))
        cp._o_display_messages.pop(message_id, None)
        if cp._o_last_display_message and cp._o_last_display_message.get('id') == message_id:
            cp._o_last_display_message = None
        logging.info(f"O-mode: ClearDisplayMessageResponse from {cp.id}: {response}")
        return response
    except Exception as e:
        logging.warning(f"O-mode ClearDisplayMessage failed for {cp.id}: {e}")
        return None


async def _execute_o_action(cp, plan, *, observed_transaction_id=None):
    cp._o_flow_state = None
    if plan is None:
        logging.info(f"O-mode: no proactive action for {cp.id} (session_index={_o_session_index(cp)})")
        return

    op = plan.get('op')

    if op == 'set_display':
        sent, pending = await _o_send_set_from_config(
            cp,
            plan,
            observed_transaction_id=observed_transaction_id,
        )
        if pending:
            cp._o_flow_state = {'op': 'await_transaction', 'plan': deepcopy(plan)}
            logging.info(f"O-mode: waiting for transaction context before SetDisplayMessage to {cp.id}")
        return

    if op == 'set_then_get':
        sent, pending = await _o_send_set_from_config(cp, plan.get('set', {}), observed_transaction_id=observed_transaction_id)
        if pending:
            cp._o_flow_state = {'op': 'await_transaction', 'plan': deepcopy(plan)}
            logging.info(f"O-mode: waiting for transaction context before set/get flow for {cp.id}")
            return
        if sent is None:
            return
        await asyncio.sleep(0.3)
        ids = None
        priority = None
        state = None
        filter_kind = plan.get('filter', 'all')
        if filter_kind == 'id':
            ids = [sent.get('id')]
        elif filter_kind == 'priority':
            priority = sent.get('priority')
        elif filter_kind == 'state':
            state = sent.get('state')
        elif filter_kind == 'unknown_id':
            ids = [_o_unknown_message_id(cp, sent.get('id'))]
        await _o_send_get_display_messages(cp, ids=ids, priority=priority, state=state)
        return

    if op == 'get_display':
        ids = None
        priority = None
        state = None
        filter_kind = plan.get('filter', 'all')
        last_message = cp._o_last_display_message or {}
        if filter_kind == 'id' and last_message.get('id') is not None:
            ids = [last_message.get('id')]
        elif filter_kind == 'priority':
            priority = last_message.get('priority')
        elif filter_kind == 'state':
            state = last_message.get('state')
        elif filter_kind == 'unknown_id':
            ids = [_o_unknown_message_id(cp, last_message.get('id'))]
        await _o_send_get_display_messages(cp, ids=ids, priority=priority, state=state)
        return

    if op == 'set_then_clear':
        sent, pending = await _o_send_set_from_config(cp, plan.get('set', {}), observed_transaction_id=observed_transaction_id)
        if pending:
            cp._o_flow_state = {'op': 'await_transaction', 'plan': deepcopy(plan)}
            logging.info(f"O-mode: waiting for transaction context before set/clear flow for {cp.id}")
            return
        if sent is None:
            return
        await asyncio.sleep(0.3)
        if plan.get('clear_known', True):
            clear_id = sent.get('id')
        else:
            clear_id = _o_unknown_message_id(cp, sent.get('id'))
        await _o_send_clear_display_message(cp, clear_id)
        return

    if op == 'clear_display_unknown':
        await _o_send_clear_display_message(cp, _o_unknown_message_id(cp))
        return

    if op == 'set_replace_same_id':
        first_sent, pending = await _o_send_set_from_config(cp, plan.get('first', {}), observed_transaction_id=observed_transaction_id)
        if pending:
            cp._o_flow_state = {'op': 'await_transaction', 'plan': deepcopy(plan)}
            logging.info(f"O-mode: waiting for transaction context before replace flow for {cp.id}")
            return
        if first_sent is None:
            return
        await asyncio.sleep(0.3)
        await _o_send_set_from_config(
            cp,
            plan.get('second', {}),
            observed_transaction_id=observed_transaction_id,
            forced_message_id=first_sent.get('id'),
        )
        return

    logging.warning(f"O-mode: unknown action plan {plan!r} for {cp.id}")


async def _o_handle_transaction_event(cp, *, transaction_id):
    if _active_cp_instance.get(cp.id) is not cp:
        return
    if transaction_id is None:
        return
    state = cp._o_flow_state or {}
    if state.get('op') != 'await_transaction':
        return
    plan = state.get('plan')
    if not isinstance(plan, dict):
        return
    cp._o_flow_state = {'op': 'transaction_dispatching'}
    await asyncio.sleep(0.2)
    await _execute_o_action(cp, plan, observed_transaction_id=transaction_id)


async def _delayed_o_action(cp, idx, delay=2):
    """Execute an O-mode action after a delay of silence from the CP."""
    this_task = asyncio.current_task()
    try:
        await asyncio.sleep(delay)
        if not cp._connection.open:
            return
        if not (0 <= idx < len(_SP1_O_PROVISIONING)):
            return
        plan = _SP1_O_PROVISIONING[idx]
        cp._o_action_fired_for_session = True
        if _o_pending_action_task.get(cp.id) is this_task:
            del _o_pending_action_task[cp.id]
        logging.info(f"O-mode action #{idx} for {cp.id}: {plan}")
        await _execute_o_action(cp, plan)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logging.warning(f"O-mode action failed for {cp.id}: {e}")
    finally:
        if _o_pending_action_task.get(cp.id) is this_task:
            del _o_pending_action_task[cp.id]


def _rollback_k_index_on_disconnect(cp):
    return


async def _k_handle_transaction_event(cp, *, event_type_text, trigger_reason_text,
                                      charging_state_text, transaction_id):
    """Handle transaction-driven smart charging actions for later K tests."""
    if cp.id not in _k_mode_active:
        return

    idx = _k_session_index(cp)
    if idx < 0:
        return

    txn_id = transaction_id or _k_latest_transaction_id.get(cp.id)
    if txn_id is None:
        return

    is_charging_transition = (
        event_type_text == 'Updated'
        and trigger_reason_text == 'ChargingStateChanged'
        and charging_state_text == 'Charging'
    )
    if not is_charging_transition:
        return

    # K_55: if EV schedule exceeded limits and was rejected, renegotiate.
    if idx == 26 and cp._k_renegotiation_pending and not cp._k_initiated_set_sent:
        cp._k_renegotiation_pending = False
        cp._k_initiated_set_sent = True
        await asyncio.sleep(0.5)
        await _k_send_tx_profile_for_transaction(cp, txn_id)
        return

    # K_58/K_59: CSMS-initiated renegotiation after charging transition.
    if idx in (28, 29) and not cp._k_initiated_set_sent:
        cp._k_initiated_set_sent = True
        await asyncio.sleep(0.5)
        await _k_send_tx_profile_for_transaction(cp, txn_id)
        return

    # K_60: send TxProfile for ongoing transaction.
    if idx == 30 and not cp._k_tx_profile_sent:
        cp._k_tx_profile_sent = True
        await asyncio.sleep(0.5)
        await _k_send_tx_profile_for_transaction(cp, txn_id)
        return

    # K_70: send two different profiles for the ongoing transaction context.
    if idx == 31 and not cp._k_multi_profile_sent:
        cp._k_multi_profile_sent = True
        profile1 = _k_profile(
            _k_next_profile_id(),
            'TxDefaultProfile',
            'Absolute',
            6.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        profile2 = _k_profile(
            _k_next_profile_id(),
            'ChargingStationMaxProfile',
            'Absolute',
            8.0,
            include_start_schedule=True,
            include_valid_window=True,
        )
        await asyncio.sleep(0.5)
        await _k_send_set_charging_profile(cp, CONFIGURED_EVSE_ID, profile1)
        await asyncio.sleep(0.5)
        await _k_send_set_charging_profile(cp, 0, profile2)


# ─── Test Mode Actions ───────────────────────────────────────────────────────

async def execute_test_mode_actions(cp, security_profile):
    """Execute CSMS-initiated actions based on the CP's configured test mode.

    Actions fire only once per CP to prevent re-triggering on reconnections
    (e.g., TC_A_09 reconnects with new password, TC_A_11 reconnects with new cert).
    Profile upgrade uses its own state machine for multi-step flows.
    """
    await asyncio.sleep(1)

    test_mode = get_test_mode_for_cp(cp.id)
    if not test_mode:
        return

    fired = cp_action_fired.get(cp.id, set())

    try:
        if test_mode == 'password_update':
            if 'password_update' not in fired:
                await _action_password_update(cp)
                cp_action_fired.setdefault(cp.id, set()).add('password_update')

        elif test_mode in ('cert_renewal_cs', 'cert_renewal_v2g', 'cert_renewal_combined'):
            if test_mode not in fired:
                trigger_map = {
                    'cert_renewal_cs': 'SignChargingStationCertificate',
                    'cert_renewal_v2g': 'SignV2GCertificate',
                    'cert_renewal_combined': 'SignCombinedCertificate',
                }
                await _action_trigger_cert_renewal(cp, trigger_map[test_mode])
                cp_action_fired.setdefault(cp.id, set()).add(test_mode)

        elif test_mode == 'profile_upgrade':
            await _action_profile_upgrade(cp, security_profile)

        elif test_mode == 'clear_cache':
            if 'clear_cache' not in fired:
                await _action_clear_cache(cp)
                cp_action_fired.setdefault(cp.id, set()).add('clear_cache')

        elif test_mode == 'get_local_list_version':
            if 'get_local_list_version' not in fired:
                await _action_get_local_list_version(cp)
                cp_action_fired.setdefault(cp.id, set()).add('get_local_list_version')

        elif test_mode == 'send_local_list_full':
            if 'send_local_list_full' not in fired:
                await _action_send_local_list_full(cp)
                cp_action_fired.setdefault(cp.id, set()).add('send_local_list_full')

        elif test_mode == 'send_local_list_diff_update':
            if 'send_local_list_diff_update' not in fired:
                await _action_send_local_list_diff_update(cp)
                cp_action_fired.setdefault(cp.id, set()).add('send_local_list_diff_update')

        elif test_mode == 'send_local_list_diff_remove':
            if 'send_local_list_diff_remove' not in fired:
                await _action_send_local_list_diff_remove(cp)
                cp_action_fired.setdefault(cp.id, set()).add('send_local_list_diff_remove')

        elif test_mode == 'send_local_list_full_empty':
            if 'send_local_list_full_empty' not in fired:
                await _action_send_local_list_full_empty(cp)
                cp_action_fired.setdefault(cp.id, set()).add('send_local_list_full_empty')

    except Exception as e:
        logging.error(f"Test mode action failed for {cp.id}: {e}")


# ─── Auto-Detect Actions ─────────────────────────────────────────────────────

async def auto_detect_and_execute(cp, security_profile):
    """Auto-detect whether the CP is waiting for a CSMS-initiated action.

    Strategy: wait briefly after connection. If any message is received from
    the CP (boot or otherwise), skip proactive actions — the CP is driving
    the flow (B-test boots, C-test Authorize/TransactionEvent).

    If no message is received within the timeout AND the connection is still
    open, the CP is waiting for a CSMS-initiated action (A-test password
    update, cert renewal, etc., or C-test ClearCache).

    Session detection:
    - A-session: first "waiting" connections arrive before any reactive ones
    - C-session: reactive connections (CP sends non-boot messages) appear
      first, then "waiting" connections need C-specific actions (clear_cache)
    """
    # Skip if this CP is being controlled via the HTTP trigger API
    if cp.id in _trigger_session_active:
        logging.info(f"Auto-detect: skipping for {cp.id} (trigger-controlled)")
        return

    # Wait to see if CP sends any message
    try:
        await asyncio.wait_for(cp._any_message_received.wait(), timeout=1.5)
        # CP sent a message — determine type
        if cp._boot_received.is_set():
            # Boot received — handled by provisioning (B tests) or quiet (A tests)
            logging.info(f"Auto-detect: boot received from {cp.id} (SP{security_profile}) - no action")
        else:
            # Non-boot message — reactive connection (C tests)
            _reactive_mode_detected.add(cp.id)
            logging.info(f"Auto-detect: reactive connection from {cp.id} (SP{security_profile}) - no action")
        return
    except asyncio.TimeoutError:
        pass

    # Check if the connection is still alive
    if not cp._connection.open:
        logging.info(f"Auto-detect: connection already closed for {cp.id} - skipping")
        return

    # Determine which action to perform based on session mode and counter
    key = (cp.id, security_profile)

    # E-session: use E-specific actions (takes precedence over C-mode)
    if cp.id in _e_mode_active:
        idx = _e_action_index.get(cp.id, 0)
        if idx < len(_SP1_E_PROVISIONING):
            trigger, action = _SP1_E_PROVISIONING[idx]
            if trigger == 'silent':
                _e_action_index[cp.id] = idx + 1
                _auto_detect_used.add(cp.id)
                txn_id = _e_cp_transactions.get(cp.id)
                logging.info(f"Auto-detect: E-mode {cp.id} silent action #{idx} -> {action}")
                try:
                    await _execute_e_action(cp, action, txn_id)
                except Exception as e:
                    logging.error(f"E-mode silent action failed for {cp.id}: {e}")
        return

    if security_profile == 1 and cp.id in _reactive_mode_detected:
        # C-session: use C-specific actions (clear_cache)
        counter = _auto_action_counter_c.get(key, 0)
        actions = _AUTO_SP1_ACTIONS_C
        _auto_action_counter_c[key] = counter + 1
    else:
        # A-session or SP2/SP3: use standard actions
        counter = _auto_action_counter.get(key, 0)
        if security_profile == 1:
            actions = _AUTO_SP1_ACTIONS
        elif security_profile == 2:
            actions = _AUTO_SP2_ACTIONS
        else:
            actions = _AUTO_SP3_ACTIONS
        _auto_action_counter[key] = counter + 1

    if counter >= len(actions):
        logging.info(f"Auto-detect: no more actions for {cp.id} SP{security_profile} "
                     f"(counter={counter})")
        return

    action = actions[counter]
    _auto_detect_used.add(cp.id)

    logging.info(f"Auto-detect: {cp.id} SP{security_profile} action #{counter} -> {action}")

    try:
        await _execute_auto_action(cp, action, security_profile)
    except Exception as e:
        logging.error(f"Auto-detect action failed for {cp.id}: {e}")


async def _execute_auto_action(cp, action, security_profile):
    """Execute a specific auto-detected action."""
    trigger_map = {
        'cert_renewal_cs': 'SignChargingStationCertificate',
        'cert_renewal_v2g': 'SignV2GCertificate',
        'cert_renewal_combined': 'SignCombinedCertificate',
    }

    if action == 'password_update':
        await _action_password_update(cp)

    elif action in trigger_map:
        await _action_trigger_cert_renewal(cp, trigger_map[action])
        # Mark state as cert_renewed so profile_upgrade can skip cert step
        cp_test_state[cp.id] = 'cert_renewed'

    elif action == 'profile_upgrade':
        await _action_profile_upgrade(cp, security_profile)

    elif action == 'clear_cache':
        await _action_clear_cache(cp)


async def _action_password_update(cp):
    """TC_A_09/A_10: Send SetVariablesRequest to change BasicAuthPassword.

    Pre-sets the new password before sending so it's accepted for reconnection
    even if cp.call() doesn't complete (test may close the connection after
    receiving the request). Since _check_password accepts both old and new
    passwords, this is safe regardless of whether the CP accepts or rejects.
    """
    new_password = NEW_BASIC_AUTH_PASSWORD
    # Pre-set so reconnection with new password works even if cp.call() hangs
    cp_passwords[cp.id] = new_password
    logging.info(f"Sending SetVariablesRequest(BasicAuthPassword) to {cp.id}")

    try:
        response = await asyncio.wait_for(
            cp.call(call.SetVariables(
                set_variable_data=[{
                    'component': {'name': 'SecurityCtrlr'},
                    'variable': {'name': 'BasicAuthPassword'},
                    'attribute_value': new_password,
                }]
            )),
            timeout=10,
        )

        if response.set_variable_result:
            for result in response.set_variable_result:
                status = result.get('attribute_status', '') if isinstance(result, dict) \
                    else str(getattr(result, 'attribute_status', ''))
                if 'accepted' in str(status).lower():
                    logging.info(f"Password updated for {cp.id}")
                else:
                    logging.info(f"Password update rejected for {cp.id} (status={status})")
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Password update cp.call did not complete for {cp.id}: {e}")


async def _action_trigger_cert_renewal(cp, trigger_type):
    """TC_A_11-14: Send TriggerMessageRequest to initiate certificate renewal.
    The CP will respond, then send SignCertificateRequest which is handled
    by on_sign_certificate -> _send_certificate_signed.
    """
    logging.info(f"Sending TriggerMessageRequest({trigger_type}) to {cp.id}")
    try:
        response = await asyncio.wait_for(
            cp.call(call.TriggerMessage(requested_message=trigger_type)),
            timeout=10,
        )
        logging.info(f"TriggerMessageResponse from {cp.id}: {response}")
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"TriggerMessage cp.call did not complete for {cp.id}: {e}")


async def _action_profile_upgrade(cp, security_profile):
    """TC_A_19: Upgrade security profile.
    For SP2->SP3: first connection does cert renewal, second does upgrade.
    For SP1->SP2: first connection does upgrade directly.
    """
    state = cp_test_state.get(cp.id, 'initial')

    if state == 'initial' and security_profile == 2:
        # SP2 -> SP3: Need cert renewal first (Memory State)
        logging.info(f"Profile upgrade: cert renewal phase for {cp.id}")
        await _action_trigger_cert_renewal(cp, 'SignChargingStationCertificate')
        cp_test_state[cp.id] = 'cert_renewed'
    elif state in ('initial', 'cert_renewed'):
        # Ready for the actual profile upgrade
        await _action_send_profile_upgrade(cp, security_profile)
    else:
        logging.info(f"Profile upgrade: no action for {cp.id} (state={state})")


async def _action_send_profile_upgrade(cp, current_sp):
    """Send SetNetworkProfile + SetVariables + Reset for profile upgrade.

    Sets cp_min_security_profile BEFORE sending Reset because the test
    closes the connection immediately after receiving Reset (simulating reboot),
    so cp.call(Reset) may not receive the response.
    """
    new_sp = current_sp + 1
    if new_sp > 3:
        logging.info(f"Profile upgrade: already at SP{current_sp}, cannot upgrade beyond SP3")
        cp_test_state[cp.id] = 'upgraded'
        return
    slot = 1

    # Step 1: SetNetworkProfileRequest
    logging.info(f"Sending SetNetworkProfileRequest(SP{new_sp}) to {cp.id}")
    await cp.call(call.SetNetworkProfile(
        configuration_slot=slot,
        connection_data={
            'ocpp_version': 'OCPP20',
            'ocpp_transport': 'JSON',
            'ocpp_csms_url': CSMS_WSS_URL,
            'message_timeout': MESSAGE_TIMEOUT,
            'security_profile': new_sp,
            'ocpp_interface': OCPP_INTERFACE,
        }
    ))

    # Step 3: SetVariablesRequest(NetworkConfigurationPriority)
    logging.info(f"Sending SetVariablesRequest(NetworkConfigurationPriority={slot}) to {cp.id}")
    await cp.call(call.SetVariables(
        set_variable_data=[{
            'component': {'name': 'OCPPCommCtrlr'},
            'variable': {'name': 'NetworkConfigurationPriority'},
            'attribute_value': str(slot),
        }]
    ))

    # Pre-set security profile BEFORE Reset: the test closes the connection
    # immediately after receiving Reset (simulating reboot), so cp.call(Reset)
    # may never receive the response.
    cp_min_security_profile[cp.id] = new_sp
    cp_test_state[cp.id] = 'upgraded'
    logging.info(f"Minimum security profile for {cp.id} set to {new_sp}")

    # Step 5: ResetRequest (response may not arrive - test closes connection)
    logging.info(f"Sending ResetRequest to {cp.id}")
    try:
        await asyncio.wait_for(
            cp.call(call.Reset(type='Immediate')),
            timeout=10,
        )
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Reset cp.call did not complete for {cp.id}: {e}")


async def _action_clear_cache(cp):
    """TC_C_37, TC_C_38: Send ClearCacheRequest."""
    logging.info(f"Sending ClearCacheRequest to {cp.id}")
    response = await cp.call(call.ClearCache())
    logging.info(f"ClearCacheResponse from {cp.id}: {response}")


async def _action_get_local_list_version(cp):
    """TC_D_08, TC_D_09: Send GetLocalListVersionRequest."""
    logging.info(f"Sending GetLocalListVersionRequest to {cp.id}")
    response = await cp.call(call.GetLocalListVersion())
    logging.info(f"GetLocalListVersionResponse from {cp.id}: {response}")


async def _action_send_local_list_full(cp):
    """TC_D_01: Send SendLocalListRequest with updateType=Full, non-empty list."""
    logging.info(f"Sending SendLocalListRequest(Full) to {cp.id}")
    response = await cp.call(call.SendLocalList(
        version_number=1,
        update_type='Full',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
            {
                'id_token': {'id_token': 'D001002', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
        ]
    ))
    logging.info(f"SendLocalListResponse from {cp.id}: {response}")


async def _action_send_local_list_diff_update(cp):
    """TC_D_02: Send SendLocalListRequest with updateType=Differential, add entries."""
    logging.info(f"Sending SendLocalListRequest(Differential, add) to {cp.id}")
    response = await cp.call(call.SendLocalList(
        version_number=2,
        update_type='Differential',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
                'id_token_info': {'status': 'Accepted'},
            },
        ]
    ))
    logging.info(f"SendLocalListResponse from {cp.id}: {response}")


async def _action_send_local_list_diff_remove(cp):
    """TC_D_03: Send SendLocalListRequest with updateType=Differential, remove entries."""
    logging.info(f"Sending SendLocalListRequest(Differential, remove) to {cp.id}")
    response = await cp.call(call.SendLocalList(
        version_number=3,
        update_type='Differential',
        local_authorization_list=[
            {
                'id_token': {'id_token': 'D001001', 'type': 'Central'},
            },
        ]
    ))
    logging.info(f"SendLocalListResponse from {cp.id}: {response}")


async def _action_send_local_list_full_empty(cp):
    """TC_D_04: Send SendLocalListRequest with updateType=Full, empty list."""
    logging.info(f"Sending SendLocalListRequest(Full, empty) to {cp.id}")
    response = await cp.call(call.SendLocalList(
        version_number=1,
        update_type='Full',
    ))
    logging.info(f"SendLocalListResponse from {cp.id}: {response}")


# ─── Auth Helpers ─────────────────────────────────────────────────────────────

def _check_password(cp_id, provided_password):
    """Check if the provided password matches any valid password for this CP.

    Accepts both the original configured password and any CSMS-updated password.
    This allows tests to reconnect with either the old or new password after
    a SetVariablesRequest(BasicAuthPassword) flow (TC_A_09 uses the new password,
    TC_A_10 uses the old password after rejecting the change).
    """
    if provided_password == BASIC_AUTH_CP_PASSWORD:
        return True
    if cp_id in cp_passwords and provided_password == cp_passwords[cp_id]:
        return True
    return False


def _decode_basic_auth(auth_header):
    """Decode a Basic auth header. Returns (username, password) or None."""
    if not auth_header or not auth_header.startswith('Basic '):
        return None
    try:
        encoded = auth_header.split(' ', 1)[1]
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username, password
    except (base64.binascii.Error, UnicodeDecodeError, ValueError):
        return None


def _unauthorized_response():
    return (
        http.HTTPStatus.UNAUTHORIZED,
        [('WWW-Authenticate', 'Basic realm="Access to CSMS"')],
        b'HTTP 401 Unauthorized\n'
    )


# ─── WS Server (Port 9000, SP1: Basic Auth) ─────────────────────────────────

async def ws_process_request(path, request_headers):
    """Validate Basic Auth and subprotocol for the WS (non-TLS) server."""
    cp_id = path.strip('/')

    # Reject unsupported WebSocket subprotocol at HTTP level
    requested_protocols = request_headers.get('Sec-WebSocket-Protocol', '')
    if requested_protocols:
        protos = [p.strip() for p in requested_protocols.split(',')]
        if 'ocpp2.0.1' not in protos:
            logging.warning(f"WS: Unsupported subprotocol(s) from {cp_id}: {protos}")
            return (
                http.HTTPStatus.BAD_REQUEST,
                [],
                b'Unsupported WebSocket subprotocol\n',
            )

    # Reject if CP has been upgraded beyond SP1
    min_sp = cp_min_security_profile.get(cp_id, 1)
    if min_sp > 1:
        logging.warning(f"WS: {cp_id} requires SP{min_sp}, rejecting SP1 connection")
        return _unauthorized_response()

    credentials = _decode_basic_auth(request_headers.get('Authorization'))
    if credentials is None:
        logging.warning(f"WS: No valid auth from {cp_id}")
        return _unauthorized_response()

    username, password = credentials

    if username == cp_id and _check_password(cp_id, password):
        logging.info(f"WS: Authorized {cp_id} (SP1)")
        return None
    else:
        logging.warning(f"WS: Bad credentials for {cp_id} (user={username})")
        return _unauthorized_response()


async def on_connect_ws(websocket, path):
    """Handle WS (non-TLS) connections - Security Profile 1."""
    if not _check_subprotocol(websocket):
        return

    cp_id = path.strip('/')
    cp = ChargePointHandler(cp_id, websocket)
    cp._security_profile = 1
    _active_cp_instance[cp_id] = cp

    test_mode = get_test_mode_for_cp(cp_id)
    if test_mode:
        asyncio.create_task(execute_test_mode_actions(cp, security_profile=1))
    else:
        asyncio.create_task(auto_detect_and_execute(cp, security_profile=1))

    try:
        await cp.start()
    except ConnectionClosedOK:
        logging.info(f'WS: {cp_id} disconnected')
    finally:
        _rollback_k_index_on_disconnect(cp)
        _trigger_session_active.discard(cp_id)
        if _active_cp_instance.get(cp_id) is cp:
            del _active_cp_instance[cp_id]


# ─── WSS Server (Port 8082, SP2: TLS+Auth, SP3: mTLS) ───────────────────────

async def wss_process_request(path, request_headers):
    """Validate auth for the WSS (TLS) server.
    SP2: Basic Auth header required.
    SP3: No auth header (client cert validated at TLS level).
    """
    cp_id = path.strip('/')

    # Reject unsupported WebSocket subprotocol at HTTP level
    requested_protocols = request_headers.get('Sec-WebSocket-Protocol', '')
    if requested_protocols:
        protos = [p.strip() for p in requested_protocols.split(',')]
        if 'ocpp2.0.1' not in protos:
            logging.warning(f"WSS: Unsupported subprotocol(s) from {cp_id}: {protos}")
            return (
                http.HTTPStatus.BAD_REQUEST,
                [],
                b'Unsupported WebSocket subprotocol\n',
            )

    min_sp = cp_min_security_profile.get(cp_id, 1)

    auth_header = request_headers.get('Authorization')
    if auth_header:
        # SP2 path: Basic Auth over TLS
        if min_sp > 2:
            logging.warning(f"WSS: {cp_id} requires SP{min_sp}, rejecting SP2")
            return _unauthorized_response()

        credentials = _decode_basic_auth(auth_header)
        if credentials is None:
            return _unauthorized_response()

        username, password = credentials

        if username == cp_id and _check_password(cp_id, password):
            logging.info(f"WSS: Authorized {cp_id} (SP2)")
            return None
        else:
            logging.warning(f"WSS: Bad credentials for {cp_id}")
            return _unauthorized_response()
    else:
        # SP3 path: mTLS (client cert verified at TLS handshake level)
        # Only accept no-auth if the CP is known to be SP3
        if min_sp < 3:
            logging.warning(f"WSS: {cp_id} has no auth header and min_sp={min_sp}, rejecting (SP3 requires min_sp>=3)")
            return _unauthorized_response()
        logging.info(f"WSS: No auth header for {cp_id} - SP3 (mTLS)")
        return None


async def on_connect_wss(websocket, path):
    """Handle WSS (TLS) connections - Security Profile 2 or 3."""
    if not _check_subprotocol(websocket):
        return

    cp_id = path.strip('/')
    auth_header = websocket.request_headers.get('Authorization')
    security_profile = 2 if auth_header else 3

    cp = ChargePointHandler(cp_id, websocket)
    cp._security_profile = security_profile
    _active_cp_instance[cp_id] = cp

    test_mode = get_test_mode_for_cp(cp_id)
    if test_mode:
        asyncio.create_task(execute_test_mode_actions(cp, security_profile))
    else:
        asyncio.create_task(auto_detect_and_execute(cp, security_profile))

    try:
        await cp.start()
    except ConnectionClosedOK:
        logging.info(f'WSS: {cp_id} disconnected (SP{security_profile})')
    finally:
        _rollback_k_index_on_disconnect(cp)
        _trigger_session_active.discard(cp_id)
        if _active_cp_instance.get(cp_id) is cp:
            del _active_cp_instance[cp_id]


# ─── Shared Helpers ──────────────────────────────────────────────────────────

def _check_subprotocol(websocket):
    """Validate WebSocket subprotocol negotiation."""
    try:
        requested = websocket.request_headers['Sec-WebSocket-Protocol']
    except KeyError:
        logging.info("No subprotocol requested. Closing.")
        asyncio.create_task(websocket.close())
        return False

    if websocket.subprotocol:
        logging.info("Subprotocol matched: %s", websocket.subprotocol)
        return True
    else:
        logging.warning("Subprotocol mismatch | Available: %s, Requested: %s",
                        websocket.available_subprotocols, requested)
        asyncio.create_task(websocket.close())
        return False


def create_server_ssl_context():
    """Create SSL context for the WSS server.

    Loads both ECDSA and RSA server certificates so that OpenSSL can
    auto-select the right one based on the negotiated cipher suite
    (A00.FR.318: ECDHE-ECDSA ciphers use the EC cert, TLS_RSA ciphers
    use the RSA cert).
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    # Include RSA key exchange ciphers required by OCPP 2.0.1 (disabled by
    # default at SECLEVEL=2 because they lack forward secrecy).
    ctx.set_ciphers('DEFAULT:AES128-GCM-SHA256:AES256-GCM-SHA384:@SECLEVEL=1')
    # ECDSA certificate (for TLS_ECDHE_ECDSA_WITH_AES_* ciphers)
    ctx.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
    # RSA certificate (for TLS_RSA_WITH_AES_* ciphers)
    if os.path.exists(SERVER_RSA_CERT) and os.path.exists(SERVER_RSA_KEY):
        ctx.load_cert_chain(certfile=SERVER_RSA_CERT, keyfile=SERVER_RSA_KEY)
    else:
        logging.warning("RSA server cert not found - TLS_RSA_WITH_AES_* ciphers won't work")
    ctx.load_verify_locations(cafile=CA_CERT)
    # CERT_OPTIONAL: accept with or without client cert;
    # if cert IS provided, it must be valid (signed by our CA)
    ctx.verify_mode = ssl.CERT_OPTIONAL
    return ctx


# ─── HTTP Trigger API Server ──────────────────────────────────────────────────
# Lightweight TCP-based HTTP server for test triggers (no extra dependencies).
# Tests POST to these endpoints to make the CSMS send OCPP messages to CPs.

def _camel_to_snake(name):
    """Convert camelCase to snake_case for the ocpp library."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _convert_keys_to_snake(obj):
    """Recursively convert dict keys from camelCase to snake_case."""
    if isinstance(obj, dict):
        return {_camel_to_snake(k): _convert_keys_to_snake(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_keys_to_snake(item) for item in obj]
    return obj


def _trigger_respond(writer, status_code, body_dict):
    """Send an HTTP JSON response and close the connection."""
    body = json.dumps(body_dict).encode()
    header = (
        f"HTTP/1.1 {status_code} OK\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode()
    writer.write(header + body)


async def _handle_trigger_http(reader, writer):
    """Handle a single HTTP request on the trigger API port."""
    try:
        # Read request line
        request_line = await asyncio.wait_for(reader.readline(), timeout=5)
        if not request_line:
            return
        parts = request_line.decode().strip().split(' ')
        if len(parts) < 2:
            _trigger_respond(writer, 400, {'error': 'Bad request'})
            return
        method, path = parts[0], parts[1]

        # Read headers
        content_length = 0
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=5)
            if line in (b'\r\n', b'\n', b''):
                break
            if line.lower().startswith(b'content-length:'):
                content_length = int(line.split(b':')[1].strip())

        # Read body
        body = {}
        if content_length > 0:
            raw = await asyncio.wait_for(reader.readexactly(content_length), timeout=5)
            body = json.loads(raw.decode())

        # Route
        result = await _route_trigger(method, path, body)
        _trigger_respond(writer, result.get('status', 200), result.get('body', {}))
    except Exception as e:
        logging.error(f"Trigger API error: {e}")
        try:
            _trigger_respond(writer, 500, {'error': str(e)})
        except Exception:
            pass
    finally:
        try:
            await writer.drain()
            writer.close()
        except Exception:
            pass


async def _route_trigger(method, path, body):
    """Route an HTTP trigger request to the appropriate handler."""
    if method != 'POST':
        return {'status': 405, 'body': {'error': 'Method not allowed'}}

    # Global endpoint: /api/octt/set-basic-auth-password
    if path == '/api/octt/set-basic-auth-password':
        return await _trigger_set_basic_auth_password(body)

    # Version-scoped endpoints: /api/octt/2.0.1/{station_id}/{action}
    prefix = '/api/octt/2.0.1/'
    if not path.startswith(prefix):
        return {'status': 404, 'body': {'error': f'Unknown path: {path}'}}

    remainder = path[len(prefix):]
    parts = remainder.split('/', 1)
    if len(parts) < 2:
        return {'status': 400, 'body': {'error': 'Missing action in path'}}

    station_id = parts[0]
    action_path = parts[1]

    # Mark CP as trigger-controlled (suppress auto-detect)
    _trigger_session_active.add(station_id)

    # Route by action
    if action_path == 'update-basic-auth-password':
        return await _trigger_update_basic_auth_password(station_id, body)
    elif action_path == 'trigger-message':
        return await _trigger_send_trigger_message(station_id, body)
    elif action_path.startswith('call/'):
        action_name = action_path[5:]  # strip 'call/'
        return await _trigger_send_call(station_id, action_name, body)
    elif action_path == 'set-security-profile':
        return await _trigger_set_security_profile(station_id, body)
    elif action_path == 'set-pending-boot':
        return await _trigger_set_pending_boot(station_id, body)
    elif action_path == 'set-items-per-message':
        return await _trigger_set_items_per_message(station_id, body)
    elif action_path == 'get-variables':
        return await _trigger_get_variables(station_id, body)
    elif action_path == 'set-variables':
        return await _trigger_set_variables(station_id, body)
    else:
        return {'status': 404, 'body': {'error': f'Unknown action: {action_path}'}}


def _find_cp(station_id):
    """Look up the active ChargePointHandler instance for a station."""
    cp = _active_cp_instance.get(station_id)
    if cp is None:
        raise ValueError(f"No active connection for station {station_id}")
    return cp


async def _trigger_update_basic_auth_password(station_id, body):
    """Handle update-basic-auth-password: send SetVariables(BasicAuthPassword)."""
    cp = _find_cp(station_id)
    new_password = NEW_BASIC_AUTH_PASSWORD
    # Pre-set so reconnection works even if cp.call() doesn't complete
    cp_passwords[station_id] = new_password
    logging.info(f"Trigger: Sending SetVariablesRequest(BasicAuthPassword) to {station_id}")

    try:
        response = await asyncio.wait_for(
            cp.call(call.SetVariables(
                set_variable_data=[{
                    'component': {'name': 'SecurityCtrlr'},
                    'variable': {'name': 'BasicAuthPassword'},
                    'attribute_value': new_password,
                }]
            )),
            timeout=10,
        )
        result_list = []
        if response.set_variable_result:
            for r in response.set_variable_result:
                status = r.get('attribute_status', '') if isinstance(r, dict) \
                    else str(getattr(r, 'attribute_status', ''))
                result_list.append({'status': str(status)})
                if 'accepted' in str(status).lower():
                    logging.info(f"Trigger: Password updated for {station_id}")
        return {'status': 200, 'body': {'result': result_list}}
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Trigger: Password update did not complete for {station_id}: {e}")
        return {'status': 200, 'body': {'result': 'timeout', 'message': str(e)}}


async def _trigger_send_trigger_message(station_id, body):
    """Handle trigger-message: send TriggerMessageRequest."""
    cp = _find_cp(station_id)
    requested_message = body.get('requestedMessage', '')
    logging.info(f"Trigger: Sending TriggerMessageRequest({requested_message}) to {station_id}")

    try:
        response = await asyncio.wait_for(
            cp.call(call.TriggerMessage(requested_message=requested_message)),
            timeout=10,
        )
        logging.info(f"Trigger: TriggerMessageResponse from {station_id}: {response}")
        return {'status': 200, 'body': {'status': str(getattr(response, 'status', response))}}
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Trigger: TriggerMessage did not complete for {station_id}: {e}")
        return {'status': 200, 'body': {'result': 'timeout', 'message': str(e)}}


async def _trigger_send_call(station_id, action_name, body):
    """Handle call/{action}: send an arbitrary OCPP CALL message."""
    cp = _find_cp(station_id)
    # Convert camelCase body keys to snake_case for the ocpp library
    snake_body = _convert_keys_to_snake(body)
    logging.info(f"Trigger: Sending {action_name} to {station_id} with {snake_body}")

    # Look up the call class dynamically
    call_cls = getattr(call, action_name, None)
    if call_cls is None:
        return {'status': 400, 'body': {'error': f'Unknown OCPP action: {action_name}'}}

    try:
        response = await asyncio.wait_for(
            cp.call(call_cls(**snake_body)),
            timeout=10,
        )
        # Convert response to a serializable dict
        resp_data = {}
        if hasattr(response, '__dataclass_fields__'):
            for field_name in response.__dataclass_fields__:
                resp_data[field_name] = getattr(response, field_name)
        else:
            resp_data = {'response': str(response)}
        logging.info(f"Trigger: {action_name} response from {station_id}: {resp_data}")
        return {'status': 200, 'body': resp_data}
    except (asyncio.TimeoutError, Exception) as e:
        logging.warning(f"Trigger: {action_name} did not complete for {station_id}: {e}")
        return {'status': 200, 'body': {'result': 'timeout', 'message': str(e)}}


async def _trigger_set_security_profile(station_id, body):
    """Handle set-security-profile: update cp_min_security_profile."""
    sp = body.get('security_profile')
    if sp is None:
        return {'status': 400, 'body': {'error': 'Missing security_profile'}}
    cp_min_security_profile[station_id] = int(sp)
    logging.info(f"Trigger: Set security profile for {station_id} to {sp}")
    return {'status': 200, 'body': {'ok': True}}


async def _trigger_set_basic_auth_password(body):
    """Handle set-basic-auth-password: update cp_passwords directly."""
    station_id = body.get('station_id')
    password = body.get('password')
    if not station_id or password is None:
        return {'status': 400, 'body': {'error': 'Missing station_id or password'}}
    cp_passwords[station_id] = password
    logging.info(f"Trigger: Set basic auth password for {station_id}")
    return {'status': 200, 'body': {'ok': True}}


async def _trigger_set_pending_boot(station_id, body):
    """Handle set-pending-boot: flag provisioning state."""
    pending = body.get('pending', True)
    # Store pending state for the station
    if pending:
        cp_test_state[station_id] = 'pending_boot'
        logging.info(f"Trigger: Set pending boot for {station_id}")
    else:
        cp_test_state.pop(station_id, None)
        logging.info(f"Trigger: Cleared pending boot for {station_id}")
    return {'status': 200, 'body': {'ok': True}}


async def _trigger_set_items_per_message(station_id, body):
    """Handle set-items-per-message: store ItemsPerMessage limits."""
    # Store limits for the station (used by get-variables/set-variables handlers)
    key = f'{station_id}_items_per_message'
    cp_test_state[key] = body
    logging.info(f"Trigger: Set items per message for {station_id}: {body}")
    return {'status': 200, 'body': {'ok': True}}


async def _trigger_get_variables(station_id, body):
    """Handle get-variables: send batched GetVariablesRequest(s)."""
    cp = _find_cp(station_id)
    get_variable_data = body.get('getVariableData', [])
    snake_data = _convert_keys_to_snake(get_variable_data)
    logging.info(f"Trigger: Sending GetVariablesRequest to {station_id} ({len(snake_data)} items)")

    # Check for items-per-message limit
    limit_key = f'{station_id}_items_per_message'
    limits = cp_test_state.get(limit_key, {})
    items_limit = limits.get('get_variables', 0)

    all_results = []
    if items_limit and items_limit > 0:
        # Split into batches
        for i in range(0, len(snake_data), items_limit):
            batch = snake_data[i:i + items_limit]
            try:
                response = await asyncio.wait_for(
                    cp.call(call.GetVariables(get_variable_data=batch)),
                    timeout=10,
                )
                if hasattr(response, 'get_variable_result'):
                    for r in response.get_variable_result:
                        all_results.append(r if isinstance(r, dict) else str(r))
            except (asyncio.TimeoutError, Exception) as e:
                logging.warning(f"Trigger: GetVariables batch failed for {station_id}: {e}")
    else:
        try:
            response = await asyncio.wait_for(
                cp.call(call.GetVariables(get_variable_data=snake_data)),
                timeout=10,
            )
            if hasattr(response, 'get_variable_result'):
                for r in response.get_variable_result:
                    all_results.append(r if isinstance(r, dict) else str(r))
        except (asyncio.TimeoutError, Exception) as e:
            logging.warning(f"Trigger: GetVariables failed for {station_id}: {e}")

    return {'status': 200, 'body': {'getVariableResult': all_results}}


async def _trigger_set_variables(station_id, body):
    """Handle set-variables: send batched SetVariablesRequest(s)."""
    cp = _find_cp(station_id)
    set_variable_data = body.get('setVariableData', [])
    snake_data = _convert_keys_to_snake(set_variable_data)
    logging.info(f"Trigger: Sending SetVariablesRequest to {station_id} ({len(snake_data)} items)")

    # Check for items-per-message limit
    limit_key = f'{station_id}_items_per_message'
    limits = cp_test_state.get(limit_key, {})
    items_limit = limits.get('set_variables', 0)

    all_results = []
    if items_limit and items_limit > 0:
        for i in range(0, len(snake_data), items_limit):
            batch = snake_data[i:i + items_limit]
            try:
                response = await asyncio.wait_for(
                    cp.call(call.SetVariables(set_variable_data=batch)),
                    timeout=10,
                )
                if hasattr(response, 'set_variable_result'):
                    for r in response.set_variable_result:
                        all_results.append(r if isinstance(r, dict) else str(r))
            except (asyncio.TimeoutError, Exception) as e:
                logging.warning(f"Trigger: SetVariables batch failed for {station_id}: {e}")
    else:
        try:
            response = await asyncio.wait_for(
                cp.call(call.SetVariables(set_variable_data=snake_data)),
                timeout=10,
            )
            if hasattr(response, 'set_variable_result'):
                for r in response.set_variable_result:
                    all_results.append(r if isinstance(r, dict) else str(r))
        except (asyncio.TimeoutError, Exception) as e:
            logging.warning(f"Trigger: SetVariables failed for {station_id}: {e}")

    return {'status': 200, 'body': {'setVariableResult': all_results}}


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    logging.info(f"Starting demo CSMS 2.0.1")
    logging.info(f"-------------------------")


    # Start WS server (SP1: Basic Auth, no TLS)
    ws_server = await websockets.serve(
        on_connect_ws,
        '0.0.0.0',
        WS_PORT,
        process_request=ws_process_request,
        subprotocols=['ocpp2.0.1'],
    )
    logging.info(f"WS  server started on port {WS_PORT}")

    # Start WSS server (SP2 + SP3: TLS) if certs exist
    wss_server = None
    if os.path.exists(SERVER_CERT) and os.path.exists(SERVER_KEY):
        ssl_ctx = create_server_ssl_context()
        wss_server = await websockets.serve(
            on_connect_wss,
            '0.0.0.0',
            WSS_PORT,
            process_request=wss_process_request,
            subprotocols=['ocpp2.0.1'],
            ssl=ssl_ctx,
        )
        logging.info(f"WSS server started on port {WSS_PORT}")
    else:
        logging.warning("TLS cert files not found - WSS server not started. "
                        "Run: python generate_certs.py")

    # Start HTTP trigger API server
    trigger_server = await asyncio.start_server(
        _handle_trigger_http, '0.0.0.0', TRIGGER_PORT)
    logging.info(f"Trigger API server started on port {TRIGGER_PORT}")

    if CP_ACTIONS:
        logging.info(f"Per-CP test actions: {CP_ACTIONS}")
    elif TEST_MODE:
        logging.info(f"Global test mode: '{TEST_MODE}'")
    else:
        logging.info("Auto-detect mode: will determine actions based on CP behavior")

    logging.info("------------------------------------------------------------")
    logging.info("CSMS 2.0.1 simulator started.")
    logging.info("This implementation should be used only for testing the tzi-OCTT suite.")
    logging.info("It is not intended for production or general-purpose use.")
    logging.info("")

    tasks = [ws_server.wait_closed(), trigger_server.serve_forever()]
    if wss_server:
        tasks.append(wss_server.wait_closed())
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
