"""
Test case name      Soft Reset
Test case Id        TC_014_CSMS
Profile             Core
Section             3.5. Core Profile - Resetting Happy Flow / 3.5.2. Soft Reset
Protocol            OCPP 1.6J
Document reference  Table 134, Page 119/176

System under test   Central System (CSMS)

Description         This scenario is used to soft reset a Charge Point.
Purpose             To test if the Central System is able to trigger a soft reset.

Prerequisite(s)     n/a

Test Scenario
1. The Central System sends a Reset.req to the Charge Point with type = "Soft".
2. The Charge Point responds with a Reset.conf with status = "Accepted".
3. The Charge Point sends a BootNotification.req (simulating reboot after soft reset).
4. The Central System responds with a BootNotification.conf with status = "Accepted".
5. The Charge Point sends a StatusNotification.req for each connector (including connectorId=0)
   with status = "Available".
6. The Central System responds with a StatusNotification.conf for each StatusNotification.req.

Validations
- Step 1: Reset.req field "type" must be "Soft".
- Step 2: Reset.conf field "status" must be "Accepted".
- Step 4: BootNotification.conf field "status" must be "Accepted".
- Step 5: StatusNotification.req field "status" must be "Available".
"""
