# OCPP 2.1 Edition 2 errata 2026-09: impact on the CSMS tests

Generated 2026-11-23 by ocpp-doc-parser. Affected test headers carry the entries verbatim in an `Errata` section (struck-through text appears as `[removed: ...]`).

## Tests removed by the errata

- **TC_Q_102_CSMS** (Q/test_tc_q_102_csms.py): 5.6. Page 60 - (2026-02) - TC_Q_102_CSMS - Test case removed; 6.3.18. Page 1336 - (2026-02) - TC_Q_102_CSMS - Test case removed

## Tests added by the errata

- **TC_A_111_CSMS** (A/test_tc_a_111_csms.py): 5.3. Page 50 & 56 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added; 6.1.1. Page 15 & 970 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added
- **TC_A_112_CSMS** (A/test_tc_a_112_csms.py): 5.3. Page 50 & 56 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added; 6.1.1. Page 15 & 970 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added

## Part 6 (test case) errata

| Entry | Affected tests / states |
|---|---|
| 6.1.1. Page 15 & 970 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added | - |
| 6.3.1. Page 1022 - 1024 - (2026-04) - TC_C_47_CSMS/TC_C_48_CSMS/TC_C_49_CSMS - Removed configuration variable masterPassGroupId | TC_C_47_CSMS, TC_C_48_CSMS, TC_C_49_CSMS |
| 6.3.2. Page 877/878 - (2026-02) - TC_Q_130_CS - BPT manual actions updated | - |
| 6.3.3. Page 944 - (2026-02) - Reusable state Iso1511820V2xControlBpt - BPT manual actions updated | - |
| 6.3.4. Page 1100/1101 - (2026-02) - TC_E_117_CSMS - Updated prerequisites and SetChargingProfileRequest tool validations | TC_E_117_CSMS |
| 6.3.5. Page 1006 - (2026-02) - TC_B_105_CSMS - Manual action added | TC_B_105_CSMS |
| 6.3.6. Page 1002 - (2026-02) - TC_B_100_CSMS - Manual action added and tool validations updated | TC_B_100_CSMS |
| 6.3.7. Page 1007/1008 - (2026-02) - TC_B_116_CSMS - | TC_B_116_CSMS |
| 6.3.8. Page 1026 - (2026-06) - TC_C_51_CSMS - Corrected OCSP response and removed post scenario validations | TC_C_51_CSMS |
| 6.3.9. Page 1038 - (2026-02) - TC_C_119_CSMS / TC_C_120_CSMS / TC_C_125_CSMS / TC_C_126_CSMS - Added missing triggerReason and stoppedReason | TC_C_119_CSMS, TC_C_120_CSMS, TC_C_125_CSMS, TC_C_126_CSMS |
| 6.3.10. Page 1046/1047 - (2026-02) - TC_C_131_CSMS - Use idToken from the RequestStartTransactionRequest, which contains the PspRef | TC_C_131_CSMS |
| 6.3.11. Page 1046/1048/1049 - (2026-02) - TC_C_131_CSMS/TC_C_132_CSMS/TC_C_133_CSMS - Sharedsecret configuration variable added | TC_C_131_CSMS, TC_C_132_CSMS, TC_C_133_CSMS |
| 6.3.12. Page 1094/1095 - (2026-02) - TC_E_110_CSMS - Added missing Authorization request to initiate transaction | TC_E_110_CSMS |
| 6.3.13. Page 1096/1097 - (2026-02) - TC_E_111_CSMS - Added missing Authorization request to initiate transaction | TC_E_111_CSMS |
| 6.3.14. Page 1333 - (2026-02) - TC_O_101_CSMS - Updated tool validations | TC_O_101_CSMS |
| 6.3.15. Page 1210 - (2026-02) - TC_K_109_CSMS - Additional test case steps added | TC_K_109_CSMS |
| 6.3.16. Page 1264/1265/1266 - (2026-09) - TC_M_100_CSMS / TC_M_26_CSMS / TC_M_28_CSMS - Included iso15118SchemaVersion information | TC_M_100_CSMS, TC_M_26_CSMS, TC_M_28_CSMS |
| 6.3.17. Page 1304-1306 - (2026-02) - TC_N_102_CSMS/TC_N_103_CSMS - added without userinfo | TC_N_102_CSMS, TC_N_103_CSMS |
| 6.3.18. Page 1336 - (2026-02) - TC_Q_102_CSMS - Test case removed | TC_Q_102_CSMS |
| 6.3.19. Page 1309 - (2026-02) - TC_N_105_CSMS - Install usable monitor and send a NotifyPeriodicEventStream | TC_N_105_CSMS |
| 6.3.20. Page 1339/1340 - (2026-02) - TC_Q_107_CSMS - Test case updated | TC_Q_107_CSMS |
| 6.3.21. Page 1359 - (2026-02) - TC_R_107_CSMS - Removed NotifyDERStartStopRequest and added ReportDERControlRequest | TC_R_107_CSMS |
| 6.3.22. Page 1365 - 1367 - (2026-02) - TC_S_103_CSMS - Test case updated | TC_S_103_CSMS |
| 6.3.23. Page 1383 - (2026-04) - Additional validation added for certificateStatus | reusable state ISO15118-20 transaction just started |

## Part 5 (certification profile) errata

| Entry | Affected tests / states |
|---|---|
| 5.1. Page 20 - (2026-02) - TC_C_100_CS - Test case removed | - |
| 5.2. Page 28 - (2026-06) - TC_E_39_CS - Only applicable for TxStopPoint Authorized | - |
| 5.3. Page 50 & 56 - (2026-09) - TC_A_111_CSMS & TC_A_112_CS/CSMS - Test cases added | - |
| 5.4. Page 54 - (2026-09) - TC_K/Q_XXX_CS - Update CSMS conditions Smart Charging & Bidirectional Power Transfer testcases | - |
| 5.5. Page 58 - (2026-09) - TC_K_53_CS / TC_K_54_CS / TC_K_56_CS - Test cases made conditional based on ISO 15118-2 support | - |
| 5.6. Page 60 - (2026-02) - TC_Q_102_CSMS - Test case removed | TC_Q_102_CSMS |
| 5.7. Page 61 - (2026-02) - TC_R_101_CS - Test case removed | - |

## Part 2 (specification) errata

| Entry | Affected tests / states |
|---|---|
| 2.1. Page 13 - (2026-02) - Updated reference 17 and added new references | - |
| 2.2. Page 24 - (2026-02) - Inclusion of RFC 8441 for HTTP/2 | - |
| 2.3. Page 24 - (2026-02) - A00.FR.308 - Additional requirement references | TC_A_01_CSMS (use case A00), TC_A_02_CSMS (use case A00), TC_A_03_CSMS (use case A00), TC_A_04_CSMS (use case A00), TC_A_06_CSMS (use case A00), TC_A_07_CSMS (use case A00), TC_A_08_CSMS (use case A00) |
| 2.4. Page 26 - (2026-02) - A00.FR.403 - Additional requirement references | TC_A_01_CSMS (use case A00), TC_A_02_CSMS (use case A00), TC_A_03_CSMS (use case A00), TC_A_04_CSMS (use case A00), TC_A_06_CSMS (use case A00), TC_A_07_CSMS (use case A00), TC_A_08_CSMS (use case A00) |
| 2.5. Page 82 - (2026-04) - B12 - Reset with ongoing transaction allows wait for cable disconnection | TC_B_21_CSMS (use case B12), TC_B_22_CSMS (use case B12), TC_B_26_CSMS (use case B12), TC_B_27_CSMS (use case B12) |
| 2.6. Page 27 - (2026-02) - A00.FR.411 - Additional requirement references | TC_A_01_CSMS (use case A00), TC_A_02_CSMS (use case A00), TC_A_03_CSMS (use case A00), TC_A_04_CSMS (use case A00), TC_A_06_CSMS (use case A00), TC_A_07_CSMS (use case A00), TC_A_08_CSMS (use case A00) |
| 2.7. Page 37 - (2026-02) - A02.FR.02 - Requirement reference correction | TC_A_11_CSMS (use case A02), TC_A_12_CSMS (use case A02), TC_A_14_CSMS (use case A02) |
| 2.8. Page 41 - (2026-02) - A03.FR.02 - Requirement reference correction | - |
| 2.9. Page 41 - (2026-02) - A03.FR.02 Only applies in security profile 3 [1167] | - |
| 2.10. Page 103 - (2026-09) - C07 Figure 26 is not binding [1343] - 2.10.1. Updated sequence diagrams for Authorization using Contract Certificates | TC_C_50_CSMS (use case C07), TC_C_51_CSMS (use case C07), TC_C_52_CSMS (use case C07) |
| 2.11. Page 140 - (2026-06) - C22.FR.01/02 - clarify "without receipt information" [1286] | TC_C_119_CSMS (use case C22), TC_C_120_CSMS (use case C22) |
| 2.12. Page 283 - (2026-02) - I06.FR.03 - added note about privacy [715] | - |
| 2.13. Page 227 - (2026-06) - New F01.FR.27 and F02.FR.28 for evseId in RequestStartTransactionRequest [1281] | TC_F_01_CSMS (use case F01), TC_F_02_CSMS (use case F02), TC_F_03_CSMS (use case F02), TC_F_04_CSMS (use case F02), TC_K_37_CSMS (use case F01) |
| 2.14. Page 334 - (2026-09) - K01 - added missing requirement to reject ExternalConstraints from CSMS [1327] | TC_K_01_CSMS (use case K01), TC_K_02_CSMS (use case K01), TC_K_03_CSMS (use case K01), TC_K_100_CSMS (use case K01), TC_K_101_CSMS (use case K01), TC_K_102_CSMS (use case K01), TC_K_104_CSMS (use case K01), TC_K_106_CSMS (use case K01), TC_K_109_CSMS (use case K01), TC_K_10_CSMS (use case K01), TC_K_15_CSMS (use case K01), TC_K_19_CSMS (use case K01), TC_K_60_CSMS (use case K01) |
| 2.15. Page 415 - (2026-04) - L01.FR.04 - removed ECSchnorr algorithm option and clarify the signature verification the Charging Station must do | TC_L_01_CSMS (use case L01), TC_L_02_CSMS (use case L01), TC_L_03_CSMS (use case L01), TC_L_04_CSMS (use case L01), TC_L_05_CSMS (use case L01), TC_L_06_CSMS (use case L01), TC_L_07_CSMS (use case L01), TC_L_08_CSMS (use case L01), TC_L_09_CSMS (use case L01), TC_L_10_CSMS (use case L01), TC_L_11_CSMS (use case L01), TC_L_13_CSMS (use case L01) |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.1. Page 319 - Smart Charging Profile Purpose | - |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.2. Page 334 - Set Charging Profile | TC_K_01_CSMS (use case K01), TC_K_02_CSMS (use case K01), TC_K_03_CSMS (use case K01), TC_K_100_CSMS (use case K01), TC_K_101_CSMS (use case K01), TC_K_102_CSMS (use case K01), TC_K_104_CSMS (use case K01), TC_K_106_CSMS (use case K01), TC_K_109_CSMS (use case K01), TC_K_10_CSMS (use case K01), TC_K_15_CSMS (use case K01), TC_K_19_CSMS (use case K01), TC_K_60_CSMS (use case K01) |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.3. Page 342 - Central Smart Charging | - |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.4. Page 346 - Local Smart Charging | - |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.5. Page 366 - Get Charging Profile | TC_K_29_CSMS (use case K09), TC_K_30_CSMS (use case K09), TC_K_31_CSMS (use case K09), TC_K_32_CSMS (use case K09), TC_K_33_CSMS (use case K09), TC_K_34_CSMS (use case K09), TC_K_35_CSMS (use case K09), TC_K_36_CSMS (use case K09) |
| 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.6. Page 364 - External Limits with Local Controller | - |
| 2.17. Page 392 - (2026-06) - K18.FR.17/K19.FR.13 InvalidMessageSequence must be InvalidMessageSeq | TC_K_115_CSMS (use case K19), TC_K_126_CSMS (use case K19) |
| 2.18. Page 502 - (2026-02) - Improved description of LocalLoadBalancing | - |
| 2.19. Page 505 - (2026-06) - Update table in Q2.2 Limits and setpoints per operation mode [1180] | - |
| 2.20. Page 507 - (2026-09) - New generic V2X requirement for Mode 3 fallback [1361] | - |
| 2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.1. Page 509 - Use case Q01 - Update of remark | TC_Q_102_CSMS (use case Q01), TC_Q_103_CSMS (use case Q01) |
| 2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.2. Page 512 - Use case Q02 - Update of scenario description | TC_Q_102_CSMS (use case Q01), TC_Q_103_CSMS (use case Q01), TC_Q_107_CSMS (use case Q02) |
| 2.21. Page 511 - (2026-09) - Q01.FR.02 - EVCCID not known at start when using EIM [1317] - 2.21.3. Page 163 - Added EVCCID to E 1.5. Clarification for optional fields | TC_Q_102_CSMS (use case Q01), TC_Q_103_CSMS (use case Q01) |
| 2.22. Page 531 - (2026-02) - Use case Q09 has improved description of LocalLoadBalancing | TC_Q_124_CSMS (use case Q09) |
| 2.23. Page 533 - (2026-02) - Use case Q09 has improved sequence diagram | TC_Q_124_CSMS (use case Q09) |
| 2.24. Page 534 - (2026-02) - Use case Q09 has improved requirements | TC_Q_124_CSMS (use case Q09) |
| 2.25. Page 554 - (2026-06) - Typo in derChargingParameters field in R02 and R03. [1231] | - |
| 2.26. Page 559 - (2026-09) - R04.FR.01 only applies to DC stations [1325] | TC_R_107_CSMS (use case R04) |
| 2.27. Page 653 - (2026-09) - Fixed descriptions of GradientType [1346] | - |
| 2.28. Page 655 - (2026-06) - LimitMaxDischargeType pctMaxDischargePower should be required [1270] | - |
| 2.29. Page 666 - (2026-02) - Updated description of StreamDataElementType [1160] | - |
| 2.30. Page 687 - (2026-06) - DERControlEnumType value PowerMonitoringMustTrip is not a DER control [1270] | - |
| 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.1. DisabledIdTokenTypes | - |
| 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.2. MacAddressInAdditionalInfo | - |
| 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.3. Appendix: Add MacAddress to additionalInfo types | - |
| 2.32. Page 746 - (2026-09) - New configuration variable RemoteStartWithoutEvseId [1311] - 2.32.1. RemoteStartWithoutEvseId | - |
| 2.33. Page 782 - (2026-06) - New optional ISO15118ProtocolEnabled variable [1252] - 2.33.1. ISO15118ProtocolEnabled | - |
| 2.34. Page 783 - (2026-09) - New variable ISO15118Ctrlr.DisableOCSPPrefetching [1362] - 2.34.1. ISO15118DisableOCSPPrefetching | - |
| 2.34. Page 783 - (2026-09) - New variable ISO15118Ctrlr.DisableOCSPPrefetching [1362] - 2.34.2. Updated M06 requirements accordingly | TC_M_24_CSMS (use case M06) |
| 2.35. Page 785 & Appendix 3.2 - (2026-06) - Added EnergyRequest to ConnectedEV [1318] | - |
| 2.36. Page 786 - (2026-06) - Updated values ConnectedEV for CHAdeMO [1192] | - |
| 2.37. Page 792 - (2026-02) - New configuration variable AutoThresholds | - |

## Entries not tied to a specific CSMS test

General specification changes (references, data types, new variables) and Charging Station-only entries. They can still matter for a CSMS implementation.

- Part 2: 2.1. Page 13 - (2026-02) - Updated reference 17 and added new references
- Part 2: 2.2. Page 24 - (2026-02) - Inclusion of RFC 8441 for HTTP/2
- Part 2: 2.8. Page 41 - (2026-02) - A03.FR.02 - Requirement reference correction
- Part 2: 2.9. Page 41 - (2026-02) - A03.FR.02 Only applies in security profile 3 [1167]
- Part 2: 2.12. Page 283 - (2026-02) - I06.FR.03 - added note about privacy [715]
- Part 2: 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.1. Page 319 - Smart Charging Profile Purpose
- Part 2: 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.3. Page 342 - Central Smart Charging
- Part 2: 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.4. Page 346 - Local Smart Charging
- Part 2: 2.16. Page 319, 334, 342, 346 - (2026-09) - CSMS cannot send LocalGeneration charging profile (2) [1327] - 2.16.6. Page 364 - External Limits with Local Controller
- Part 2: 2.18. Page 502 - (2026-02) - Improved description of LocalLoadBalancing
- Part 2: 2.19. Page 505 - (2026-06) - Update table in Q2.2 Limits and setpoints per operation mode [1180]
- Part 2: 2.20. Page 507 - (2026-09) - New generic V2X requirement for Mode 3 fallback [1361]
- Part 2: 2.25. Page 554 - (2026-06) - Typo in derChargingParameters field in R02 and R03. [1231]
- Part 2: 2.27. Page 653 - (2026-09) - Fixed descriptions of GradientType [1346]
- Part 2: 2.28. Page 655 - (2026-06) - LimitMaxDischargeType pctMaxDischargePower should be required [1270]
- Part 2: 2.29. Page 666 - (2026-02) - Updated description of StreamDataElementType [1160]
- Part 2: 2.30. Page 687 - (2026-06) - DERControlEnumType value PowerMonitoringMustTrip is not a DER control [1270]
- Part 2: 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.1. DisabledIdTokenTypes
- Part 2: 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.2. MacAddressInAdditionalInfo
- Part 2: 2.31. Page 736 - (2026-09) - New variable DisabledIdTokenTypes [1363] - 2.31.3. Appendix: Add MacAddress to additionalInfo types
- Part 2: 2.32. Page 746 - (2026-09) - New configuration variable RemoteStartWithoutEvseId [1311] - 2.32.1. RemoteStartWithoutEvseId
- Part 2: 2.33. Page 782 - (2026-06) - New optional ISO15118ProtocolEnabled variable [1252] - 2.33.1. ISO15118ProtocolEnabled
- Part 2: 2.34. Page 783 - (2026-09) - New variable ISO15118Ctrlr.DisableOCSPPrefetching [1362] - 2.34.1. ISO15118DisableOCSPPrefetching
- Part 2: 2.35. Page 785 & Appendix 3.2 - (2026-06) - Added EnergyRequest to ConnectedEV [1318]
- Part 2: 2.36. Page 786 - (2026-06) - Updated values ConnectedEV for CHAdeMO [1192]
- Part 2: 2.37. Page 792 - (2026-02) - New configuration variable AutoThresholds
- Part 5: 5.1. Page 20 - (2026-02) - TC_C_100_CS - Test case removed
- Part 5: 5.2. Page 28 - (2026-06) - TC_E_39_CS - Only applicable for TxStopPoint Authorized
- Part 5: 5.4. Page 54 - (2026-09) - TC_K/Q_XXX_CS - Update CSMS conditions Smart Charging & Bidirectional Power Transfer testcases
- Part 5: 5.5. Page 58 - (2026-09) - TC_K_53_CS / TC_K_54_CS / TC_K_56_CS - Test cases made conditional based on ISO 15118-2 support
- Part 5: 5.7. Page 61 - (2026-02) - TC_R_101_CS - Test case removed
- Part 6: 6.3.2. Page 877/878 - (2026-02) - TC_Q_130_CS - BPT manual actions updated
- Part 6: 6.3.3. Page 944 - (2026-02) - Reusable state Iso1511820V2xControlBpt - BPT manual actions updated
