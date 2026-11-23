"""
Test case name      Unpublish Firmware - NoFirmware
Test case Id        TC_L_22_CSMS
Use case Id(s)      L04
Requirement(s)      N/a
System under test   CSMS

Description         Stop serving a firmware update to connected Charging Stations.

Purpose             To verify if the CSMS is able to unpublish a firmware on the local controller as described
                    at the OCPP specification.

Prerequisite(s)     n/a

Configuration State N/a

Memory State        N/a

Reusable State      N/a

Test Scenario
1. The CSMS sends a UnpublishFirmwareRequest
2. The Test System responds with a UnpublishFirmwareResponse with status NoFirmware

Tool validations
-N/a

Post scenario validations:
    - N/a
"""
