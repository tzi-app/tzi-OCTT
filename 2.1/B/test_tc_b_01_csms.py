"""
Test case name      Cold Boot Charging Station - Accepted
Test case Id        TC_B_01_CSMS
Use case Id(s)      B01
Requirement(s)      B01.FR.02

Requirement Details:
    B01.FR.02: The CSMS SHALL respond to indicate whether it will accept the Charging Station.
        Precondition: B01.FR.01 The CSMS has received BootNotificationRequest from the Charging Station.
System under test   CSMS

Description         The booting mechanism allows a Charging Station to provide some general information about
                    the Charging Station to the CSMS on startup AND it allows the Charging Station to request
                    whether it is allowed to start sending other OCPP messages.

Purpose             To verify whether the CSMS is able to accept the communications of a registered Charging
                    Station.

Prerequisite(s)     N/a

Configuration State N/a

Memory State        N/a

Reusable State(s)   N/a

Test Scenario
1. Execute Reusable State Booted

Tool validations
N/a

Post scenario validations:
    N/a
"""
