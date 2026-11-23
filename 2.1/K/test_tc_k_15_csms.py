"""
Test case name      Set Charging Profile - Not Supported
Test case Id        TC_K_15_CSMS
Use case Id(s)      K01
Requirement(s)      N/a
System under test   CSMS

Description         To enable the CSMS to influence the charging power or current drawn from a specific EVSE
                    or the entire Charging Station over a period of time. The CSMS sends a
                    SetChargingProfileRequest to the Charging Station to influence the power or current drawn
                    by EVs. The CSMS calculates a ChargingSchedule to stay within certain limits, which MAY be
                    imposed by any external system.

Purpose             To verify if the CSMS is able to send a Profile, while the charging station does not
                    support chargingprofiles, and read the response as described at the OCPP specification.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a SetChargingProfileRequest with:
    - evseId <Configured evseId> AND
    - chargingProfile.stackLevel <Configured stackLevel> AND
    - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
    - chargingProfile.chargingProfileKind Absolute AND
    - chargingProfile.chargingSchedule.startSchedule <Not omitted> AND
    - chargingProfile.chargingSchedule.chargingRateUnit <Configured ChargingRateUnit> AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.duration <Configured duration>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases> where
      <Configured numberPhases> not 3 OR
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases> or <omit>
      where <Configured numberPhases> 3
2. The Test System responds with RPC Framework: CALLERROR: NotSupported.

Tool validations
* Step 1:
    Message SetChargingProfileRequest
    - evseId <Configured evseId> AND
    - chargingProfile.stackLevel <Configured stackLevel> AND
    - chargingProfile.chargingProfilePurpose TxDefaultProfile AND
    - chargingProfile.chargingProfileKind Absolute AND
    - chargingProfile.chargingSchedule.startSchedule <Not omitted> AND
    - chargingProfile.chargingSchedule.chargingRateUnit <Configured ChargingRateUnit> AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod 0 AND
    - chargingProfile.chargingSchedule.duration <Configured duration>
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.limit 6.0 or 6000.0 AND
    - chargingProfile.chargingSchedule.chargingSchedulePeriod.numberPhases <Configured numberPhases>

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
"""
