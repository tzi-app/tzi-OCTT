"""
Test case name      EMS Control - Set Charging Profile - MaxExternalConstraintsId
Test case Id        TC_K_109_CSMS
Use case Id(s)      K01
Requirement(s)      K01.FR.80

Requirement Details:
    K01.FR.80 (2.1): CSMS SHALL choose a value for the id of a ChargingProfileType that is higher than
                     MaxExternalConstraintsId.
        Precondition: When configuration variable MaxExternalConstraintsId is set
        Note: This ensures there will not be a conflict with charging profile id’s generated at Charging
              Station to represent ChargingStationExternalConstraints profiles.
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to send a charging profile using the right id set by
                    MaxExternalConstraintsId as described at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a GetBaseReportRequest
2. The Test System responds with a GetBaseReportResponse with
    - status Accepted
3. The Test System sends a NotifyReportRequest containing
    - requestId <requestId>
    - reportData[0].component.name SmartChargingCtrlr
    - reportData[0].variable.name MaxExternalConstraintsId
    - reportData[0].variableAttribute.value 2147400000
4. The CSMS responds with a NotifyReportResponse

Manual Action: Request the CSMS to send a TxDefaultProfile Charging Profile

5. The CSMS sends a SetChargingProfileRequest
6. The Test System responds with a SetChargingProfileResponse with
    - status Accepted

Tool validations
* Step 5:
    Message SetChargingProfileRequest
    - chargingProfile.id must be greater than 2147400000

Post scenario validations:
    - N/a

Errata (OCPP 2.1 Edition 2 errata 2026-09)
    2.14. Page 334 - (2026-09) - K01 - added missing requirement to reject ExternalConstraints from CSMS
        [1327]
        (Part 2 errata - applies to this test via use case K01)
        A CSMS is forbidden to send a ChargingStationExternalConstraints profile to a charging station, but a
        matching requirement that Charging Station must reject it if it receives such a charging profile was
        missing.

        New requirement

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.62 | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to ChargingStationExternalConstraints | Charging Station SHALL respond
          with a status = Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not
          allowed from CSMS. |

    2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] -
        2.16.2. Page 334 - Set Charging Profile
        (Part 2 errata - applies to this test via use case K01)
        Added a requirement that CSMS shall not send a LocalGeneration profile and a requirement that a
        Charging Station shall reject it.

        New requirements

        | ID | Precondition | Requirement definition | Note |
        | K01.FR.63 / (2.1) | | The CSMS SHALL NOT set chargingProfilePurpose to LocalGeneration in a
          SetChargingProfileRequest. | This purpose is only received from an external system. |
        | K01.FR.64 / (2.1) | When a Charging Station receives a SetChargingProfileRequest from CSMS with
          chargingProfilePurpose set to LocalGeneration | Charging Station SHALL respond with a status =
          Rejected and optionally a statusInfo.reasonCode = UnsupportedPurpose | Purpose not allowed from
          CSMS. |

    6.3.15. Page 1210 - (2026-02) - TC_K_109_CSMS - Additional test case steps added
        The main test scenario was updated to include an initial SetVariablesRequest for
        MaxExternalConstraintsId to ensure the CSMS is accurately tested for updating the chargingProfileId.

        | Test case name | EMS Control - Set Charging Profile - MaxExternalConstraintsId |
        | Test case Id | TC_K_109_CSMS |
        | … | |

        | Main (Test scenario) | |
        | Charging Station | CSMS |
        | [removed: 2. The Test System responds with a GetBaseReportResponse with / status Accepted] |
          [removed: 1. The CSMS sends a GetBaseReportRequest] |
        | [removed: 3. The Test System sends a NotifyReportRequest containing / requestId <requestId> /
          reportData[0].component.name SmartChargingCtrlr / reportData[0].variable.name
          MaxExternalConstraintsId / reportData[0].variableAttribute.value 2147400000] | [removed: 4. The CSMS
          responds with a NotifyReportResponse] |
        | Manual Action : Configure variable MaxExternalConstraintsId on the CSMS | |
        | 2. The Test System responds with SetVariablesResponse | 1. The CSMS sends SetVariablesRequest with:
          / - variable.name MaxExternalConstraintsId / - component.name SmartChargingCtrlr / - attributeValue
          10 |
        | Manual Action: Request the CSMS to send a TxDefaultProfile Charging Profile | |

        | Main (Test scenario) | |
        | [removed: 6.] 4. The Test System responds with a SetChargingProfileResponse with / status Accepted |
          [removed: 5.] 3. The CSMS sends a SetChargingProfileRequest |
        | Manual Action : Request the CSMS to clear the charging profile with <chargingProfileId from step 3>
          | |
        | 6. The Test System responds with a ClearChargingProfileResponse with / status Accepted | 5. The CSMS
          sends a ClearChargingProfileRequest with / chargingProfileId <chargingProfileId from step 3> AND /
          chargingProfileCriteria omit |
        | Manual Action: Configure variable MaxExternalConstraintsId on the CSMS | |
        | 8. The Test System responds with SetVariablesResponse | 7. The CSMS sends SetVariablesRequest with:
          / - variable.name MaxExternalConstraintsId / - component.name SmartChargingCtrlr / - attributeValue
          2147400000 |
        | Manual Action : Request the CSMS to send a TxDefaultProfile Charging Profile | |
        | 10. The Test System responds with a SetChargingProfileResponse with / status Accepted | 9. The CSMS
          sends a SetChargingProfileRequest |

        | Tool validations |
        | * Step 3: / Message SetChargingProfileRequest / chargingProfile.id must be greater than 10 |
        | * Step 5: / Message ClearChargingProfileRequest / chargingProfile.id must be <chargingProfileId from
          step 1> |
        | * Step [removed: 5] 9: / Message SetChargingProfileRequest / chargingProfile.id must be greater than
          2147400000 |
        | Post scenario validations: / - N/a |
"""

import asyncio
import os

import pytest

from charge_point import TziChargePoint21
from reusable_states.booted import booted
from smart_charging import charging_profile, request_charging_profile
from trigger import send_call, set_variables
from utils import get_basic_auth_headers

BASIC_AUTH_CP = os.environ['CP21_SP1']
BASIC_AUTH_CP_PASSWORD = os.environ['BASIC_AUTH_CP_PASSWORD']
CONFIGURED_EVSE_ID = int(os.environ['CONFIGURED_EVSE_ID'])


def max_external_constraints_id(value):
    """The SetVariableData that sets SmartChargingCtrlr.MaxExternalConstraintsId."""
    return [{
        'component': {'name': 'SmartChargingCtrlr'},
        'variable': {'name': 'MaxExternalConstraintsId'},
        'attributeValue': str(value),
    }]


@pytest.mark.asyncio
@pytest.mark.parametrize("connection",
                         [(BASIC_AUTH_CP, get_basic_auth_headers(BASIC_AUTH_CP, BASIC_AUTH_CP_PASSWORD))],
                         indirect=True)
async def test_tc_k_109(connection):
    assert connection.open
    cp = TziChargePoint21(BASIC_AUTH_CP, connection)
    start_task = asyncio.create_task(cp.start())
    await booted(cp)

    # The scenario is the one of errata 2026-09 (6.3.15): the CSMS sets MaxExternalConstraintsId
    # itself, with a SetVariablesRequest, instead of reading it in a base report.

    # Manual Action: Configure variable MaxExternalConstraintsId on the CSMS
    # 1. The CSMS sends SetVariablesRequest with:
    #    - variable.name MaxExternalConstraintsId
    #    - component.name SmartChargingCtrlr
    #    - attributeValue 10
    # 2. The Test System responds with SetVariablesResponse
    await cp.wait_for_request(
        'SetVariables', manual_action=set_variables(BASIC_AUTH_CP, max_external_constraints_id(10)))

    # Manual Action: Request the CSMS to send a TxDefaultProfile Charging Profile
    # 3. The CSMS sends a SetChargingProfileRequest
    # 4. The Test System responds with a SetChargingProfileResponse with status Accepted
    # The request to the CSMS has no id for the charging profile: the CSMS chooses it (K01.FR.80).
    first = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Absolute', 6, profile_id=None))
    assert first.charging_profile.id > 10, \
        f"chargingProfile.id must be greater than 10 (MaxExternalConstraintsId), " \
        f"got {first.charging_profile.id}"

    # Manual Action: Request the CSMS to clear the charging profile with <chargingProfileId from
    #                step 3>
    # 5. The CSMS sends a ClearChargingProfileRequest with
    #    - chargingProfileId <chargingProfileId from step 3> AND
    #    - chargingProfileCriteria omit
    # 6. The Test System responds with a ClearChargingProfileResponse with status Accepted
    cp.set_response('ClearChargingProfile', status='Accepted')
    clear = await cp.wait_for_request(
        'ClearChargingProfile',
        manual_action=send_call(BASIC_AUTH_CP, 'ClearChargingProfile',
                                {'chargingProfileId': first.charging_profile.id}))
    assert clear.charging_profile_id == first.charging_profile.id, \
        f"Expected ClearChargingProfileRequest.chargingProfileId {first.charging_profile.id}, " \
        f"got {clear.charging_profile_id}"

    # Manual Action: Configure variable MaxExternalConstraintsId on the CSMS
    # 7. The CSMS sends SetVariablesRequest with:
    #    - variable.name MaxExternalConstraintsId
    #    - component.name SmartChargingCtrlr
    #    - attributeValue 2147400000
    # 8. The Test System responds with SetVariablesResponse
    await cp.wait_for_request(
        'SetVariables',
        manual_action=set_variables(BASIC_AUTH_CP, max_external_constraints_id(2147400000)))

    # Manual Action: Request the CSMS to send a TxDefaultProfile Charging Profile
    # 9. The CSMS sends a SetChargingProfileRequest
    # 10. The Test System responds with a SetChargingProfileResponse with status Accepted
    second = await request_charging_profile(
        cp, CONFIGURED_EVSE_ID, charging_profile('TxDefaultProfile', 'Absolute', 6, profile_id=None))
    assert second.charging_profile.id > 2147400000, \
        f"chargingProfile.id must be greater than 2147400000 (MaxExternalConstraintsId), " \
        f"got {second.charging_profile.id}"

    start_task.cancel()
