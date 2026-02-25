"""
Test case name      Remote Start Transaction with Charging Profile
Test case Id        TC_059_CSMS
Feature profile     SmartCharging
Document ref        Table 182, Section 3.19.4, Pages 156-157/176

Description         The Central System starts a transaction on a Charge Point with a ChargingProfile.
Purpose             To check whether the Central System can trigger a Charge Point to start a transaction with a
                    Charging Profile.
Prerequisite(s)     The Central System supports the Smart Charging feature profile.

Before State:
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

System under test   Central System

Test Scenario
    1.  The Central System sends a RemoteStartTransaction.req to the Charge Point.
    2.  The Charge Point responds with a RemoteStartTransaction.conf.
    3.  The Charge Point sends an Authorize.req to the Central System.
    4.  The Central System responds with an Authorize.conf.
        [The charging cable is plugged in]
    5.  The Charge Point sends a StatusNotification.req to the Central System.
    6.  The Central System responds with a StatusNotification.conf.
    7.  The Charge Point sends a StartTransaction.req to the Central System.
    8.  The Central System responds with a StartTransaction.conf.
    9.  The Charge Point sends a StatusNotification.req to the Central System.
    10. The Central System responds with a StatusNotification.conf.

Tool validations
    * Step 1:
        (Message: RemoteStartTransaction.req)
        - idTag is <Configured valid IdTag>
        - connectorId is <Configured ConnectorId>
        - chargingProfile.chargingProfilePurpose is TxProfile
        - chargingProfile.transactionId is omitted
        - The first chargingProfile.chargingSchedule.chargingSchedulePeriod.startPeriod is 0
        - csChargingProfiles.recurrencyKind is <Omitted>
        AND
        - csChargingProfiles.chargingProfileKind is Absolute or Relative
        AND
          if csChargingProfiles.chargingProfileKind is Absolute:
            - csChargingProfiles.validFrom <Not omitted> AND
            - csChargingProfiles.validTo <Not omitted> AND
            - csChargingProfiles.chargingSchedule.startSchedule <Not omitted> AND
            - csChargingProfiles.chargingSchedule.duration <Not omitted>
          if csChargingProfiles.chargingProfileKind is Relative:
            - csChargingProfiles.chargingSchedule.startSchedule <Omitted>

    * Step 2:
        (Message: RemoteStartTransaction.conf)
        - status is Accepted

    * Step 3:
        (Message: Authorize.req)
        - idTag is the idTag from step 1.

    * Step 4:
        (Message: Authorize.conf)
        - idTagInfo.status is Accepted

    * Step 5:
        (Message: StatusNotification.req)
        - status is Preparing
        - connectorId is the connectorId from step 1.

    * Step 6:
        (Message: StatusNotification.conf)
        - Response acknowledged

    * Step 7:
        (Message: StartTransaction.req)
        - idTag is the idTag from step 1.
        - connectorId is the connectorId from step 1.

    * Step 8:
        (Message: StartTransaction.conf)
        - status is Accepted

    * Step 9:
        (Message: StatusNotification.req)
        - status is Charging
        - connectorId is the connectorId from step 1.

    * Step 10:
        (Message: StatusNotification.conf)
        - Response acknowledged

Expected result(s):
    CP (Tool): n/a
    CS (SUT): The Central System has started a transaction on the Charge Point and accepts
    the transaction that is started on the Charge Point.

NOTE: Step 6 and Step 10 (StatusNotification.conf) have no explicit tool validations in the
official document - "Response acknowledged" is inferred.
NOTE: "csChargingProfiles" in the tool validations appears to be the document's alias for the
chargingProfile field in the RemoteStartTransaction.req - to be confirmed.
"""
