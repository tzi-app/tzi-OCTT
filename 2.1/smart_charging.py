"""Charging profiles for the smart charging tests of OCPP 2.1 (block K).

The profiles are given as they go on the wire (the field names of the OCPP 2.1 schemas): they
are the payloads of the trigger API calls that make the CSMS send a charging profile. The
validations are for the requests that the CSMS then sends.
"""

import os
from datetime import datetime, timezone

from authorization import CURRENT_TIME_TOLERANCE, is_current_date_time
from ocpp_messages import utc_now_iso
from trigger import send_call

# The configured values of the test cases
CHARGING_PROFILE_ID = int(os.environ['CONFIGURED_CHARGING_PROFILE_ID'])
STACK_LEVEL = int(os.environ['CONFIGURED_STACK_LEVEL'])
CHARGING_PROFILE_PURPOSE = os.environ['CONFIGURED_CHARGING_PROFILE_PURPOSE']
CHARGING_RATE_UNIT = os.environ['CONFIGURED_CHARGING_RATE_UNIT']
DURATION = int(os.environ['CONFIGURED_CHARGING_SCHEDULE_DURATION'])
NUMBER_PHASES = int(os.environ['CONFIGURED_NUMBER_PHASES'])
RECURRENCY_KIND = os.environ['CONFIGURED_RECURRENCY_KIND']
CHARGING_LIMIT_SOURCE = os.environ['CONFIGURED_CHARGING_LIMIT_SOURCE']


def limit_of(amperes, charging_rate_unit=None):
    """A limit of the test cases, given as "6.0 or 6000.0": the first in A, the second in W."""
    unit = charging_rate_unit or CHARGING_RATE_UNIT
    return float(amperes) if unit == 'A' else amperes * 1000.0


def charging_schedule(amperes, start_schedule=True, duration=True, schedule_id=1, **fields):
    """A ChargingScheduleType with one period that starts at 0 and has the given limit.

    start_schedule: the schedule starts now; False for a Relative charging profile.
    duration: the configured duration; False leaves it out.
    fields: other ChargingScheduleType fields.
    """
    schedule = {'id': schedule_id}
    if start_schedule:
        schedule['startSchedule'] = utc_now_iso()
    if duration:
        schedule['duration'] = DURATION
    schedule['chargingRateUnit'] = CHARGING_RATE_UNIT
    schedule['chargingSchedulePeriod'] = [{
        'startPeriod': 0,
        'limit': limit_of(amperes),
        'numberPhases': NUMBER_PHASES,
    }]
    schedule.update(fields)
    return schedule


def charging_profile(purpose, kind, amperes, profile_id=CHARGING_PROFILE_ID, start_schedule=None,
                     duration=True, schedule=None, **fields):
    """A ChargingProfileType with one charging schedule of one period.

    profile_id None: no id, the CSMS chooses it.
    start_schedule: by default as the kind of the profile requires (K01.FR.40, K01.FR.41).
    schedule: other ChargingScheduleType fields.
    fields: other ChargingProfileType fields, such as transactionId or recurrencyKind.
    """
    if start_schedule is None:
        start_schedule = kind in ('Absolute', 'Recurring')
    profile = {} if profile_id is None else {'id': profile_id}
    profile.update({
        'stackLevel': STACK_LEVEL,
        'chargingProfilePurpose': purpose,
        'chargingProfileKind': kind,
    })
    profile.update(fields)
    profile['chargingSchedule'] = [
        charging_schedule(amperes, start_schedule=start_schedule, duration=duration,
                          **(schedule or {}))]
    return profile


async def request_charging_profile(cp, evse_id, profile, status='Accepted'):
    """The Manual Action that makes the CSMS send a SetChargingProfileRequest with this
    charging profile, which the Test System answers with `status` (or with any other answer
    that set_response() takes). Returns the SetChargingProfileRequest of the CSMS."""
    if isinstance(status, str):
        cp.set_response('SetChargingProfile', status=status)
    else:
        cp.set_response('SetChargingProfile', status)
    return await cp.wait_for_request(
        'SetChargingProfile',
        manual_action=send_call(cp.id, 'SetChargingProfile',
                                {'evseId': evse_id, 'chargingProfile': profile}))


# ─── Tool validations ────────────────────────────────────────────────────────

def only_schedule(request):
    """The one charging schedule of the charging profile of a request."""
    schedules = request.charging_profile.charging_schedule
    assert len(schedules) == 1, f"Expected one chargingSchedule, got {len(schedules)}"
    return schedules[0]


def validate_profile(request, evse_id=None, purpose=None, kind=None, stack_level=STACK_LEVEL,
                     profile_id=None, transaction_id=None):
    """The validations of the fields of a SetChargingProfileRequest that the test cases have
    in common. A value None is not validated."""
    profile = request.charging_profile
    if evse_id is not None:
        assert request.evse_id == evse_id, \
            f"Expected SetChargingProfileRequest.evseId {evse_id}, got {request.evse_id}"
    if profile_id is not None:
        assert profile.id == profile_id, f"Expected chargingProfile.id {profile_id}, got {profile.id}"
    if stack_level is not None:
        assert profile.stack_level == stack_level, \
            f"Expected chargingProfile.stackLevel {stack_level}, got {profile.stack_level}"
    if purpose is not None:
        assert profile.charging_profile_purpose == purpose, \
            f"Expected chargingProfile.chargingProfilePurpose {purpose}, " \
            f"got {profile.charging_profile_purpose}"
    if kind is not None:
        kinds = (kind,) if isinstance(kind, str) else tuple(kind)
        assert profile.charging_profile_kind in kinds, \
            f"Expected chargingProfile.chargingProfileKind {' or '.join(kinds)}, " \
            f"got {profile.charging_profile_kind}"
    if transaction_id is not None:
        assert profile.transaction_id == transaction_id, \
            f"Expected chargingProfile.transactionId {transaction_id}, got {profile.transaction_id}"


def validate_schedule(schedule, amperes=None, start_schedule=None, duration=None,
                      charging_rate_unit=CHARGING_RATE_UNIT, number_phases=True):
    """The validations of a charging schedule of the test cases.

    amperes: chargingSchedulePeriod.startPeriod 0 and .limit <amperes>.0 (A) or <amperes>000.0
        (W), and with number_phases the numberPhases of the period.
    start_schedule: 'now', True (not omitted) or False (must be omitted); None: not validated.
    duration: True for the configured duration; None: not validated.
    """
    if charging_rate_unit is not None:
        assert schedule.charging_rate_unit == charging_rate_unit, \
            f"Expected chargingSchedule.chargingRateUnit {charging_rate_unit}, " \
            f"got {schedule.charging_rate_unit}"
    if start_schedule == 'now':
        assert schedule.start_schedule is not None and is_current_date_time(schedule.start_schedule), \
            f"Expected chargingSchedule.startSchedule now, got {schedule.start_schedule}"
    elif start_schedule is True:
        assert schedule.start_schedule is not None, "chargingSchedule.startSchedule must NOT be omitted"
    elif start_schedule is False:
        assert schedule.start_schedule is None, \
            f"chargingSchedule.startSchedule must be omitted, got {schedule.start_schedule}"
    if duration:
        assert schedule.duration == DURATION, \
            f"Expected chargingSchedule.duration {DURATION}, got {schedule.duration}"
    if amperes is not None:
        period = schedule.charging_schedule_period[0]
        assert period.start_period == 0, \
            f"Expected chargingSchedulePeriod.startPeriod 0, got {period.start_period}"
        expected = limit_of(amperes, schedule.charging_rate_unit)
        assert period.limit == expected, \
            f"Expected chargingSchedulePeriod.limit {float(amperes)} (A) or {amperes * 1000.0} (W), " \
            f"got {period.limit} {schedule.charging_rate_unit}"
        if number_phases:
            validate_number_phases(period)


def validate_number_phases(period):
    """chargingSchedulePeriod.numberPhases <Configured numberPhases> where <Configured
    numberPhases> not 3 OR <Configured numberPhases> or <omit> where <Configured numberPhases>
    3."""
    allowed = (NUMBER_PHASES, None) if NUMBER_PHASES == 3 else (NUMBER_PHASES,)
    assert period.number_phases in allowed, \
        f"Expected chargingSchedulePeriod.numberPhases {NUMBER_PHASES}" \
        f"{' or omitted' if NUMBER_PHASES == 3 else ''}, got {period.number_phases}"


def validate_validity(profile, duration=DURATION):
    """chargingProfile.validFrom now AND chargingProfile.validTo now + <Configured Charging
    Schedule Duration>."""
    assert profile.valid_from is not None and is_current_date_time(profile.valid_from), \
        f"Expected chargingProfile.validFrom now, got {profile.valid_from}"
    assert profile.valid_to is not None, "chargingProfile.validTo must not be omitted"
    valid_to = datetime.fromisoformat(profile.valid_to.upper().replace('Z', '+00:00'))
    remaining = (valid_to - datetime.now(timezone.utc)).total_seconds()
    assert abs(remaining - duration) <= CURRENT_TIME_TOLERANCE, \
        f"Expected chargingProfile.validTo now + {duration} s, got {profile.valid_to}"


def validate_start_schedule_for_kind(profile):
    """If chargingProfileKind is Relative then chargingSchedule.startSchedule must be omitted.
    If chargingProfileKind is Absolute (or Recurring) then it must NOT be omitted (K01.FR.40,
    K01.FR.41)."""
    for schedule in profile.charging_schedule:
        if profile.charging_profile_kind == 'Relative':
            assert schedule.start_schedule is None, \
                f"chargingSchedule.startSchedule must be omitted in a Relative charging profile, " \
                f"got {schedule.start_schedule}"
        elif profile.charging_profile_kind in ('Absolute', 'Recurring'):
            assert schedule.start_schedule is not None, \
                f"chargingSchedule.startSchedule must NOT be omitted in a " \
                f"{profile.charging_profile_kind} charging profile"


def validate_recurrency_kind(profile):
    """If chargingProfileKind is Recurring then recurrencyKind must NOT be omitted, else
    omitted (K01.FR.60)."""
    if profile.charging_profile_kind == 'Recurring':
        assert profile.recurrency_kind is not None, \
            "chargingProfile.recurrencyKind must NOT be omitted in a Recurring charging profile"
    else:
        assert profile.recurrency_kind is None, \
            f"chargingProfile.recurrencyKind must be omitted in a {profile.charging_profile_kind} " \
            f"charging profile, got {profile.recurrency_kind}"


def validate_part_2_requirements(profile, evse_id=None, in_request_start_transaction=False):
    """"The received Charging Profile must comply with the requirements defined at part 2
    specification": the requirements of use case K01 that a CSMS has to follow for the charging
    profile of a transaction that does not use ISO 15118.

    evse_id: the evseId of the SetChargingProfileRequest.
    in_request_start_transaction: the profile of a RequestStartTransactionRequest, which has
        no transactionId (K05).
    """
    purpose, kind = profile.charging_profile_purpose, profile.charging_profile_kind
    assert purpose not in ('ChargingStationExternalConstraints', 'LocalGeneration'), \
        f"K01.FR.22: a CSMS does not send a charging profile with purpose {purpose}"
    if purpose == 'TxProfile':
        if in_request_start_transaction:
            assert profile.transaction_id is None, \
                f"K05: the TxProfile of a RequestStartTransactionRequest has no transactionId, " \
                f"got {profile.transaction_id}"
        else:
            assert profile.transaction_id is not None, "K01.FR.03: a TxProfile has a transactionId"
        assert evse_id is None or evse_id > 0, \
            f"K01.FR.16: a TxProfile is only used with evseId > 0, got {evse_id}"
    if purpose == 'ChargingStationMaxProfile':
        assert kind != 'Relative', "K01.FR.38: a ChargingStationMaxProfile is not Relative"
    assert len(profile.charging_schedule) == 1, \
        f"K01.FR.34: one chargingSchedule, got {len(profile.charging_schedule)}"
    validate_start_schedule_for_kind(profile)
    validate_recurrency_kind(profile)
    for schedule in profile.charging_schedule:
        if purpose == 'PriorityCharging':
            assert schedule.duration is None, \
                f"K01.FR.73: no duration in a PriorityCharging profile, got {schedule.duration}"
        periods = schedule.charging_schedule_period
        assert periods[0].start_period == 0, \
            f"K01.FR.31: the startPeriod of the first chargingSchedulePeriod is 0, " \
            f"got {periods[0].start_period}"
        starts = [period.start_period for period in periods]
        assert starts == sorted(starts) and len(set(starts)) == len(starts), \
            f"K01.FR.35: the chargingSchedulePeriods are ordered by increasing startPeriod: {starts}"
        for period in periods:
            if period.phase_to_use is not None:
                assert period.number_phases == 1, \
                    f"K01.FR.19: phaseToUse only with numberPhases 1, got {period.number_phases}"
            if purpose in ('PriorityCharging', 'ChargingStationMaxProfile'):
                assert period.operation_mode in (None, 'ChargingOnly'), \
                    f"K01.FR.111: operationMode ChargingOnly or none in a {purpose} profile, " \
                    f"got {period.operation_mode}"
            if period.limit_l2 is not None or period.limit_l3 is not None:
                assert purpose == 'TxProfile', \
                    f"K01.FR.143: no limit_L2 or limit_L3 in a {purpose} profile"
                assert period.limit is not None, "K01.FR.145: limit_L2 or limit_L3 only with a limit"


def reported_profile(profile_id=CHARGING_PROFILE_ID, purpose=CHARGING_PROFILE_PURPOSE,
                     stack_level=STACK_LEVEL, amperes=6, **fields):
    """A charging profile that the Test System has, for a ReportChargingProfilesRequest
    (snake_case, as the station sends it)."""
    profile = {
        'id': profile_id,
        'stack_level': stack_level,
        'charging_profile_purpose': purpose,
        'charging_profile_kind': 'Absolute',
        'charging_schedule': [{
            'id': 1,
            'start_schedule': utc_now_iso(),
            'charging_rate_unit': CHARGING_RATE_UNIT,
            'charging_schedule_period': [{'start_period': 0, 'limit': limit_of(amperes)}],
        }],
    }
    profile.update(fields)
    return profile


# ─── Get Charging Profiles (K09) ─────────────────────────────────────────────

async def request_charging_profiles_report(cp, evse_id=None, request_id=1, **criterion):
    """The Manual Action that makes the CSMS send a GetChargingProfilesRequest, which the Test
    System answers with status Accepted. criterion: the fields of chargingProfile, with the
    field names of the schema. Returns the GetChargingProfilesRequest of the CSMS."""
    payload = {'requestId': request_id, 'chargingProfile': criterion}
    if evse_id is not None:
        payload['evseId'] = evse_id
    cp.set_response('GetChargingProfiles', status='Accepted')
    return await cp.wait_for_request(
        'GetChargingProfiles', manual_action=send_call(cp.id, 'GetChargingProfiles', payload))


def validate_get_charging_profiles(request, evse_id=None, purpose=None, stack_level=None,
                                   charging_limit_source=None, profile_id=None):
    """The tool validations of a GetChargingProfilesRequest: the evseId and each field of
    chargingProfile must have the given value, and must be omitted when that is None."""
    criterion = request.charging_profile
    fields = [
        ('evseId', request.evse_id, evse_id),
        ('chargingProfile.chargingProfilePurpose', criterion.charging_profile_purpose, purpose),
        ('chargingProfile.stackLevel', criterion.stack_level, stack_level),
        ('chargingProfile.chargingLimitSource', criterion.charging_limit_source,
         None if charging_limit_source is None else [charging_limit_source]),
        ('chargingProfile.chargingProfileId', criterion.charging_profile_id,
         None if profile_id is None else [profile_id]),
    ]
    for name, value, expected in fields:
        if expected is None:
            assert value is None, f"GetChargingProfilesRequest.{name} must be omitted, got {value}"
        else:
            assert value == expected, f"Expected GetChargingProfilesRequest.{name} {expected}, got {value}"


# ─── V2X (block Q) ───────────────────────────────────────────────────────────

# The limits and setpoints of a ChargingSchedulePeriodType, per phase
POWER_FIELDS = tuple(
    f"{name}{phase}"
    for name in ('limit', 'discharge_limit', 'setpoint', 'setpoint_reactive')
    for phase in ('', '_l2', '_l3'))


def tx_profile_id(cp, transaction_id):
    """The id of the TxProfile that the CSMS has set for a transaction, which a new TxProfile
    of that transaction replaces (K01.FR.05, K01.FR.39); the configured id when it has none."""
    for request in reversed(cp.requests_of('SetChargingProfile')):
        profile = request.charging_profile
        if profile.charging_profile_purpose == 'TxProfile' and profile.transaction_id == transaction_id:
            return profile.id
    return CHARGING_PROFILE_ID


def v2x_profile(purpose, kind, period, profile_id=CHARGING_PROFILE_ID, charging_rate_unit='W',
                **fields):
    """A ChargingProfileType with one charging schedule that has the given period, for the
    V2X test cases. period: the fields of the ChargingSchedulePeriodType besides startPeriod 0,
    as on the wire. fields: other ChargingProfileType fields."""
    schedule = {'id': 1, 'chargingRateUnit': charging_rate_unit,
                'chargingSchedulePeriod': [{'startPeriod': 0, **period}]}
    if kind in ('Absolute', 'Recurring'):
        schedule['startSchedule'] = utc_now_iso()
    profile = {} if profile_id is None else {'id': profile_id}
    profile.update({'stackLevel': STACK_LEVEL, 'chargingProfilePurpose': purpose,
                    'chargingProfileKind': kind})
    profile.update(fields)
    profile['chargingSchedule'] = [schedule]
    return profile


def periods_of(request):
    """Every charging schedule period of the charging profile of a request, with its place:
    ("chargingSchedule[0].chargingSchedulePeriod[0]", period)."""
    return [(f"chargingSchedule[{s}].chargingSchedulePeriod[{p}]", period)
            for s, schedule in enumerate(request.charging_profile.charging_schedule)
            for p, period in enumerate(schedule.charging_schedule_period)]


def validate_periods(request, operation_mode=None, omitted=(), present=()):
    """The validations of all charging schedule periods of a request: the operationMode (a
    value, or several that are allowed; None among them stands for omitted), the fields that
    must be omitted and the fields that must not be."""
    modes = operation_mode if isinstance(operation_mode, tuple) else (operation_mode,)
    for where, period in periods_of(request):
        if operation_mode is not None:
            assert period.operation_mode in modes, \
                f"Expected {where}.operationMode {' or '.join(str(mode) for mode in modes)}, " \
                f"got {period.operation_mode}"
        for name in omitted:
            assert period[name] is None, f"{where}.{name} must be omitted, got {period[name]}"
        for name in present:
            assert period[name] is not None, f"{where}.{name} must not be omitted"
