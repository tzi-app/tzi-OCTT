"""
State               Booted
System under test   CSMS
Description         This state will simulate that the Charging Station is completely power cycled. The Test
                    System end in a state where it is "booted" back up and is in idle mode.
Before
    Configuration State:    N/a
    Memory State:           N/a
    Reusable State(s):      N/a

Main

1. The Test System sends a BootNotificationRequest with reason PowerUp
   chargingStation.model <Configured model>
   chargingStation.vendorName <Configured vendorName>
2. The CSMS responds with a BootNotificationResponse
3. The Test System notifies the CSMS about the current state of all connectors.
   Message: StatusNotificationRequest
   with connectorStatus Available
   Message: NotifyEventRequest
   with trigger Delta
   actualValue "Available"
   component.name "Connector"
   variable.name "AvailabilityState"
4. The CSMS responds accordingly.

Tool validations
* Step 2: Message: BootNotificationResponse - status Accepted
Post condition      State is Booted
"""

from charge_point import TziChargePoint21


async def booted(cp: TziChargePoint21):
    # 1. The Test System sends a BootNotificationRequest with reason PowerUp, the configured
    #    model and the configured vendorName
    # 2. The CSMS responds with a BootNotificationResponse
    boot_response = await cp.send_boot_notification(reason='PowerUp')
    assert boot_response.status == 'Accepted', \
        f"Expected BootNotificationResponse.status Accepted, got {boot_response.status}"

    # 3. The Test System notifies the CSMS about the current state of all connectors.
    #    Message: StatusNotificationRequest with connectorStatus Available
    #    Message: NotifyEventRequest with trigger Delta, actualValue "Available",
    #             component.name "Connector", variable.name "AvailabilityState"
    # 4. The CSMS responds accordingly.
    await cp.send_all_connectors_status('Available')

    return boot_response
