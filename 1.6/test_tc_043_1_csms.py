"""
Test case name      Send Local Authorization List - NotSupported
Test case Id        TC_043_1_CSMS
System under test   Central System
Document reference  Table 157, Section 3.14.2, Page 136/176

Description         The Charge Point can authorize an EV driver based on a local list that is set by
                    the Central System.

Purpose             To check whether a Central System can handle a NotSupported status, after sending
                    a Local Authorization List.

Prerequisite(s)     The Central System supports the Local Auth List Management feature profile.

Before
    Configuration State(s): n/a
    Memory State(s): n/a
    Reusable State(s): n/a

Test Scenario
    Charge Point (Tool)                         Central System (SUT)
    2. The Charge Point responds with a         1. The Central System sends a
       SendLocalList.conf                          SendLocalList.req

Tool validations
    Charge Point (Tool)                         Central System (SUT)
    * Step 2:                                   * Step 1:
      (Message: SendLocalList)                    (Message: SendLocalList.req)
      - Status is NotSupported                    - updateType should be Full

Expected result(s) / behaviour
    Charge Point (Tool)                         Central System (SUT)
    n/a                                         The Central System is able to send a local
                                                list and is able to receive a NotSupported
                                                response.
"""
