"""
Test case name      Basic Authentication - Valid username/password combination
Test case Id        TC_085_CSMS
Section             3.21 Security > 3.21.1 Secure connection setup
System under test   Central System
Document ref        Table 195, pages 169-170

Description         The Charge Point uses Basic authentication to authenticate itself to the Central System, when using
                    security profile 1 or 2.

Purpose             To verify whether the Central System is able to validate the (valid) Basic authentication credentials provided
                    by the Charge Point at the connection request.

Prerequisite(s)     The Central System supports security profile 1 and/or 2.

Before (Preparations)
    Configuration State: N/a
    Memory State: N/a
    Reusable State(s): The OCTT closes the connection.

Test Scenario
    1. The Charge Point sends a HTTP upgrade request without an Authorization header to the Central System.
    2. The Central System rejects the connection upgrade request.

    3. The Charge Point sends a HTTP upgrade request with an Authorization header, containing a
       username/password combination.
    4. The Central System validates the username/password combination AND accepts the connection upgrade request.

    5. The Charge Point sends a BootNotification.req
    6. The Central System responds with a BootNotification.conf

    [Send per connector and connectorId=0.]
    7. The Charge Point sends a StatusNotification.req
    8. The Central System responds with a StatusNotification.conf

Tool Validations
    Note: The BasicAuthPassword that the tool will use to connect can be configured in two ways:
    1. When the configured value for BasicAuthPassword is >= 32 and <= 40 characters, the tool will expect that
       this is the hex encoded representation of the password.
    2. When the configured value for BasicAuthPassword is >= 16 and <= 20 characters, the tool will expect that
       this is plaintext (UTF-8) representation of the password.

    Post scenario validations: N/a

Expected result(s) / behaviour: n/a
    NOTE: Not explicitly listed in the CSMS version of the document; the corresponding CS version (TC_085_CS) shows n/a.
"""
