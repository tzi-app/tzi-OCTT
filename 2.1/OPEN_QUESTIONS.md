# OCPP 2.1 tests: open questions and decisions

Every test file in `2.1/` is implemented. Where a test description was ambiguous, disagreed with itself or with
the specification, or needed something the 2.0.1 suite has no convention for, the test makes a choice and this file
records it.

- [Part 1](#1-questions) has the choices that need an answer.
- [Part 2](#2-trigger-api-of-the-21-tests) is the trigger API that a CSMS has to provide for these tests.
- [Part 3](#3-new-settings) lists the settings added to `pytest.ini`.
- [Part 4](#4-notes-per-block) has the smaller interpretations, per block. They need no answer unless you disagree.

Not done: `CSMS_SETUP.md` does not cover the 2.1 suite yet. `README.md` describes it as experimental and points
here for the trigger API and the settings.

## 1. Questions

1. **`ocppVersion OCPP20` (TC_A_19, TC_B_42).** Both descriptions require `connectionData.ocppVersion OCPP20`. OCPP 2.1
   marks that value "no longer in use" (OCPPVersionEnumType), and the errata corrected it to `OCPP21` for TC_B_100
   only (6.3.6). The two tests check `OCPP20`, as printed. Should they check `OCPP21`?
2. **Unsupported subprotocol (TC_B_58).** Step 2 says the CSMS "does NOT upgrade the connection". OCPP-J 2.1 (part 4,
   3.3) says it must complete the handshake without a `Sec-WebSocket-Protocol` header and then close immediately. The
   test accepts both. Should only one of them pass?
3. **TC_Q_102 was removed by the errata** (5.6, 6.3.18). Its file has one skipped test that gives this reason. Delete
   the file instead?
4. **Reusable states that start or end the transaction themselves (block E).** Read literally, the named state sends
   the Started or Ended event that the scenario then sends again. The tests do this:
   - TC_E_19 (state EVDisconnected, then Ended/EVDeparted): the state's event is sent as Updated, without
     stoppedReason. 2.0.1 does the same.
   - TC_E_109, TC_E_110, TC_E_111 (state EVConnectedPreSession, then Started/ChargingStateChanged): the state only
     reports the connector Occupied and sends no TransactionEvent.
   - TC_E_20 (state EnergyTransferSuspended, then "Execute EVDisconnected"): only the main steps of EVDisconnected
     run, not its Before chain. 2.0.1 does the same.
5. **ISO 15118 tests whose reusable state is too little (block K).** TC_K_53 and TC_K_55 name only "Authorized", and
   the state of TC_K_57, TC_K_58 and TC_K_59 is blank. A negotiation needs a connected EV, and a renegotiation needs a
   schedule. The tests run Authorized + EVConnectedPreSession, and ISO15118SmartCharging for K_57/58/59, as 2.0.1
   does.
6. **TC_Q_108 has no Manual Action**, but validates specific values: TxProfile, operationMode CentralSetpoint,
   "setpoint must be 10.000". The test triggers that profile itself (`call/SetChargingProfile`) after the reusable
   state, and reads 10.000 as 10000 W. Should the CSMS instead send this profile on its own, as its answer to the
   charging needs of the state? And is 10.000 ten thousand watts or ten?
7. **Manual Action and tool validation disagree.** The tests follow the tool validation:
   - TC_N_60: the first Manual Action asks for ThresholdMonitoring of Power and the second for DeltaMonitoring of
     AvailabilityState. The validations want DeltaMonitoring first and ThresholdMonitoring second, both of
     AvailabilityState (2.0.1 makes the same choice).
   - TC_N_105: "interval of 15s and values 45" in the Manual Action, interval 10 and values 20 in the errata's
     validation (6.3.19).
   - TC_Q_124: UpperThreshold 1000 in the Manual Action, 2000 in the validation.
   - TC_G_06: the Manual Action says "to Inoperative", the validation Operative.
8. **`chargingProfile.chargingSchedule.<field>` without an index** is read as "the profile has exactly one charging
   schedule": TC_K_01, K_02, K_03, K_10, K_15, K_19, K_70, Q_108, Q_121 and Q_125 fail a profile with more. Tests whose
   description has `chargingSchedule[0]` or `[*]` do not check the number of schedules.
9. **EVSEs that the mock station does not have.** `CONFIGURED_NUMBER_OF_EVSES` is 1, but some descriptions use more,
   and the tests follow them: TC_C_47 and TC_C_49 use EVSE 1 and 2 (as 2.0.1), TC_I_106 reports `evseIds [2]`, and
   TC_S_103 (errata 6.3.22) uses slots 1-4. A CSMS that knows the EVSEs of a station needs four for `CP21_SP1`.
10. **Checks "in the CSMS UI" are not automated**: the "Check that CSMS shows ..." lines of block N, and the
    verification of TC_O_100.
11. **TC_E_107 takes two minutes.** Its description notes that the limit is reached 120 s after the start of the
    transaction, and the test really waits for that.
12. **Checks that are not a listed tool validation.** TC_A_111 and TC_A_112 check that CertificateSignedRequest has
    the requestId of the SignCertificateRequest (A02.FR.25). A station must answer Rejected to an unknown requestId
    (A02.FR.26), and the scenario has Accepted. Keep the check?
13. **New trigger endpoints.** Eight endpoints are new compared with 2.0.1 ([part 2](#2-trigger-api-of-the-21-tests)).
    Each stands for something that only the CSMS can decide or do. The alternative is always to put the values in a
    `call/{Action}` payload, and then the test only checks that the CSMS passes on what it was given. Are they
    acceptable, or should some be plain `call/{Action}` calls?

## 2. Trigger API of the 2.1 tests

The conventions are those of 2.0.1 (`CSMS_SETUP.md`, step 7): a `POST` with a JSON body under
`CSMS_TRIGGER_ADDRESS`, answered with HTTP 200 and a JSON body. `2.1/trigger.py` is the client.

### Station endpoints: `/api/octt/2.1/{stationId}/…`

| Endpoint | Body | What the CSMS does | Used by |
|---|---|---|---|
| `call/{Action}` | The OCPP request payload | Sends that CALL to the station. In `call/SetChargingProfile` the `chargingProfile.id` may be left out; the CSMS then chooses it, above `MaxExternalConstraintsId` (K01.FR.80) | See the actions below |
| `trigger-message` | TriggerMessageRequest payload | Sends TriggerMessage | F |
| `update-basic-auth-password` | none | Generates a new Basic Auth password and sets it on the station (A01) | A_09, A_10 |
| `get-variables` | `{"getVariableData": [...]}` | Sends GetVariablesRequest(s), split by ItemsPerMessageGetVariables | B_06, B_07, B_08, N |
| `set-variables` | `{"setVariableData": [...]}` | Sends SetVariablesRequest(s), split by ItemsPerMessageSetVariables | B_09, B_10, C_47, C_48, C_49, K_109, Q_124 |
| `set-pending-boot` | `{"pending": true}` or `false` | Answers the station's next BootNotification Pending or Accepted. No OCPP message | B_02, B_30, B_31 |
| `set-security-profile` | `{"security_profile": n}` | Records that the station now uses that profile. No OCPP message | A_19 |
| `clear-variable-monitoring` | `{"id": [...]}` | Sends ClearVariableMonitoringRequest(s), split by ItemsPerMessageClearVariableMonitoring (N06.FR.04) | N_18 |
| `set-network-configuration` **new** | `{"configurationSlot": n, "connectionData": {...}}` | Sets a network profile through the device model: SetVariables on `NetworkConfiguration[slot]`, with ApnEnabled and VpnEnabled chosen by the CSMS (B09.FR.29, B09.FR.30) | B_105 |
| `kiosk-payment-authorized` **new** | `{"pspRef", "evseId", "cardLast4Digits", "authorizationAmount"}` | What a payment kiosk tells the CSMS (C24). The CSMS sends RequestStartTransaction with the PspRef as a DirectPayment idToken, and sets the transaction limit | C_125, C_126 |
| `set-transaction-limit` **new** | `{"maxCost" \| "maxEnergy" \| "maxTime" \| "maxSoC", "transactionId"?}` | Configures a limit for the ongoing or next transaction. The CSMS sends it once, in the first possible TransactionEventResponse (E16.FR.02) | E_102, E_109, E_110, E_111 |
| `provide-charging-profiles` **new** | `{"enabled": bool}` | Turns providing a charging profile for charging needs on or off. Off: NotifyEVChargingNeeds is answered NoChargingProfile (K18.FR.04, K19.FR.04) | K_126 |
| `get-log` **new** | `{"logType", "scheme": "http" \| "https", "requestId"}` | Sends GetLog with the `remoteLocation` of its own log server, with userinfo. The test then uploads there: first without credentials (expects 401, errata 6.3.17), then with | N_102, N_103 |
| `update-dynamic-schedule` **new** | `{"chargingProfileId", "interval", "scheduleUpdate": {...}}` | From now on sends UpdateDynamicSchedule for that profile every `interval` seconds, until the profile is cleared (K28, Q04) | Q_109, Q_117 |

2.0.1's `set-items-per-message` is not used: the CSMS reads the limits with a GetVariablesRequest, as the descriptions
say ("Configure (using getVariablesRequest)").

### Other endpoints

| Endpoint | Body | What the CSMS does | Used by |
|---|---|---|---|
| `/api/octt/set-basic-auth-password` | `{"station_id", "password"}` | Stores a new Basic Auth password. No OCPP message | A_09 |
| `/api/octt/2.1/qr-code-payment` **new** | `{"qrUrl": "..."}` | An EV driver opened that QR code URL and paid (C25). The CSMS validates the one-time password and, for a valid URL, sends RequestStartTransaction to the station of the URL. It answers HTTP 200 for an invalid URL too | C_131, C_132, C_133 |
| `/api/octt/2.1/driver-tariff` **new** | `{"idToken": {...}, "tariff": {...} \| null}` | Sets or removes the driver-specific tariff of an idToken (I08). The test removes it again at its end | I_109 |

### Actions sent through `call/{Action}`

The tests send 49 actions this way: the 36 of the 2.0.1 suite and 13 that are new in OCPP 2.1.

> CancelReservation, ChangeAvailability, ClearCache, ClearChargingProfile, ClearDisplayMessage,
> ClearVariableMonitoring, CustomerInformation, DeleteCertificate, GetBaseReport, GetChargingProfiles,
> GetCompositeSchedule, GetDisplayMessages, GetInstalledCertificateIds, GetLocalListVersion, GetLog,
> GetMonitoringReport, GetReport, GetTransactionStatus, InstallCertificate, PublishFirmware,
> RequestStartTransaction, RequestStopTransaction, ReserveNow, Reset, SendLocalList, SetChargingProfile,
> SetDisplayMessage, SetMonitoringBase, SetMonitoringLevel, SetNetworkProfile, SetVariableMonitoring, SetVariables,
> TriggerMessage, UnlockConnector, UnpublishFirmware, UpdateFirmware

New in 2.1:

> AdjustPeriodicEventStream, AFRRSignal, ChangeTransactionTariff, ClearDERControl, ClearTariffs, GetDERControl,
> GetPeriodicEventStream, GetTariffs, NotifyAllowedEnergyTransfer, RequestBatterySwap, SetDefaultTariff,
> SetDERControl, UsePriorityCharging

## 3. New settings

All are defaults in `pytest.ini`; an environment variable of the same name overrides them.

| Setting | Default | For |
|---|---|---|
| `CP21_SP1`, `CP21_SP2`, `CP21_SP3` | the same names | The three 2.1 stations (security profiles 1, 2, 3) |
| `CSMS_NO_ACTION_WAIT` | `5` | Seconds a test waits to see that the CSMS does *not* send something |
| `PREPAID_ID_TOKEN`, `PREPAID_NO_CREDIT_ID_TOKEN` (+ `_TYPE`) | `PREPAID001`, `PREPAID002`, `ISO14443` | Prepaid cards with and without credit (TC_C_103, TC_C_104) |
| `VALID_VAT_NUMBER`, `INVALID_VAT_NUMBER` | `NL123456789B01`, `NL000000000B00` | VAT number validation (TC_C_108) |
| `CARD_LAST_4_DIGITS` | `1234` | Kiosk payments (TC_C_125, TC_C_126) |
| `QR_CODE_BASE_URL`, `QR_CODE_SHARED_SECRET` | `https://qr.example.com`, `mysharedsecret` | QR code payments (TC_C_131-133). The CSMS has the URL template `<base>/{chargingstationid}/{evse}/{totp}/{version}` and the secret |
| `CONFIGURED_HEARTBEAT_INTERVAL` | `10` | TC_B_02 |
| `CONFIGURED_EV_CONNECTION_TIMEOUT` | `5` | TC_E_39 waits this long |
| `CONFIGURED_NON_ACTIVE_CONFIGURATION_SLOT`, `CONFIGURED_APN`, `CONFIGURED_APN_USERNAME`, `CONFIGURED_APN_PASSWORD` | `2`, `internet.example.com`, `apn-user`, `apn-password` | TC_B_105 |
| `CONFIGURED_CSR_COUNTRY`, `CONFIGURED_CSR_ORGANIZATION`, `CONFIGURED_CSR_ORGANIZATIONAL_UNIT` | `NL`, `TZI Test`, `OCTT` | Certificate signing requests (A) |
| `CONFIGURED_EVCCID` | `EVCC00112233AABB` | ISO 15118-20 (K, Q) |
| `CONFIGURED_CHARGING_PROFILE_ID`, `CONFIGURED_STACK_LEVEL`, `CONFIGURED_CHARGING_PROFILE_PURPOSE`, `CONFIGURED_CHARGING_RATE_UNIT`, `CONFIGURED_CHARGING_SCHEDULE_DURATION`, `CONFIGURED_RECURRENCY_KIND`, `CONFIGURED_CHARGING_LIMIT_SOURCE` | `1`, `0`, `TxDefaultProfile`, `A`, `300`, `Daily`, `CSO` | Smart charging (K, Q) |
| `CONFIGURED_DYNAMIC_PROFILE_UPDATE_INTERVAL` | `5` | TC_Q_109 |
| `CONFIGURED_FIRMWARE_LOCATION` | `https://firmware.example.com/tzi/firmware-2.1.0.bin` | Firmware (L) |
| `CONFIGURED_PRIORITIZED_EMAIDS` | `EMAID001,EMAID002,EMAID003` | TC_M_100 |
| `CONFIGURED_LOG_LOCATION` | `https://logs.example.com/tzi-octt/` | GetLog (N) |
| `CONFIGURED_DISPLAY_MESSAGE_ID`, `_PRIORITY`, `_FORMAT`, `_STATE`, `_LANGUAGE`, `_OTHER_LANGUAGE` | `1`, `NormalCycle`, `UTF8`, `Idle`, `en`, `nl` | Display messages (O) |

## 4. Notes per block

### All blocks

- **The mock station validates every message of the CSMS** against the official OCPP 2.1 JSON schemas. The 2.0.1
  suite does not validate responses by default.
- **Timestamps are real UTC** (`ocpp_messages.utc_now_iso`). `utils.now_iso()` of the other suites stamps local time
  with a "Z".
- **Values of a CSMS request come from the trigger payload**, as in 2.0.1: charging profiles, reservation ids,
  certificates, display messages, tariffs, the transactionId of RequestStopTransaction and GetTransactionStatus.
  Most validations of such a request therefore check that the CSMS passes it on unchanged.
- **Run the suite in its own pytest session**: `pytest -p no:warnings ./2.1`. Its modules have the same names as those
  of 2.0.1 and 1.6.

### A, B: security and provisioning

- **TC_B_08**: the CSMS learns ItemsPerMessage from a GetVariablesRequest (see `set-items-per-message` in part 2).
- **TC_B_105** uses `set-network-configuration`. With plain `set-variables` the test would give ApnEnabled and
  VpnEnabled itself, and the validation could not fail.
- **Reset tests (TC_B_20 and others)** send the BootNotification on the same connection, without a reconnect, as
  2.0.1.

### C, D: authorization and local list

- **TC_C_51, TC_C_52**: the text says `<Configured valid_idtoken>`. The tests send the configured eMAID, as TC_C_50
  and the 2.0.1 tests do: C07.FR.02 requires the eMAID.
- **TC_C_103 step 4**: the text says `<cacheExpiryDateTime from step 2>`, the sequence diagram of C17 has `<now>` in
  both responses. The test accepts either.
- **TC_C_131-133**: the tests put `1` in the URL as `{version}`, as the text says. The device model lists the
  TOTPVersion value as `v1`.
- **TC_C_118**: a receipt URL that is "valid and accessible" must answer an HTTP GET with a 2xx status.
- **TC_C_48, TC_C_49**: the answer for the *valid* idToken has `groupIdToken` = the master pass group, so both are
  `GROUP001` in `pytest.ini`.
- **TC_D_02**: one Manual Action in the text, two trigger calls in the test: `call/GetLocalListVersion`, then
  `call/SendLocalList` with versionNumber `LOCAL_LIST_VERSION + 1`. So the test chooses the higher version, not the
  CSMS.
- **TC_D_04** `localAuthorizationList <Empty>`: the schema requires at least one item, so the field is left out.

### E: transactions

- **TC_E_39**: waits `CONFIGURED_EV_CONNECTION_TIMEOUT` (2.0.1 does not wait).
- **TC_E_29, E_31, E_33 (offline)**: the text has no Manual Action for GetTransactionStatusRequest; the tests use
  `call/GetTransactionStatus`, as 2.0.1. The station sends no BootNotification after it reconnects.
- **TC_E_31 step 5**: the Ended event has no stoppedReason, as in the text (2.0.1 sends EVDisconnected).
- **TC_E_102, E_109, E_110, E_111** use `set-transaction-limit`. The CSMS has to respect
  `TxCtrlr.SupportedLimits` (E16.FR.12), which the mock station reports.
- **TC_E_109**: the text has no Manual Action for the cost limit of 10. The test calls `set-transaction-limit`
  after the AuthorizeResponse, where the errata put it for TC_E_110 and TC_E_111. The CSMS must know that the station
  does not calculate cost (`TariffCostCtrlr.Enabled[Cost]` false) to send totalCost in every response. The
  CostUpdatedRequest is optional; the test waits `CSMS_NO_ACTION_WAIT` for it.
- **TC_E_108**: the validation "evseId must be <evse id>" is checked as the `evseId 0` of step 1.
  `totalUsage.energy` is mandatory in the schema but absent from the text; the test sends 11 kW x the charging
  time.
- **TC_E_102 step 3** says only "eventType Updated": sent with triggerReason MeterValuePeriodic and one meter value.
- **TC_E_113**: security event StartupOfTheDevice (the text allows it or ResetOrReboot), boot reason PowerUp.
  TC_E_117 uses ResetOrReboot, per the errata.

### F, G, H: remote control, availability, reservation

- **TC_F_01-F_04**: the TransactionEvent with triggerReason RemoteStart also has the idToken of the
  RequestStartTransactionRequest (F01.FR.04, F02.FR.05, F02.FR.12), which the step text does not list.
  "remoteStartId is <By Test System generated remoteStartID>" is read as the remoteStartId that the CSMS sent.
- **TC_F_12, TC_F_14** "evseId omitted ... for every EVSE": MeterValuesRequest.evseId is mandatory, so TC_F_12 sends
  one MeterValuesRequest per EVSE. Neither test asserts that `TriggerMessageRequest.evse` is absent: it is not a
  listed validation (2.0.1 does assert it).
- **TC_F_27** does not say which message to request: the test asks for PublishFirmwareStatusNotification, as 2.0.1.
- **TC_G_11, G_14, G_17**: "Wait for <Configured Transaction Duration>" before StopAuthorized is taken as the wait
  that StopAuthorized has itself. TC_G_11 step 6 "StatusNotification OR NotifyEvent": both are sent.
- **Block H**: the test chooses the reservation id and expiryDateTime (now + 300 s; TC_H_07: now +
  `TRANSACTION_DURATION`).

### I, J: tariff, cost and meter values

- **TC_I_01 step 3** has eventType Updated for the first event of the transaction, and no Started event: implemented
  as printed, as 2.0.1.
- **Block I prerequisites name "TariffCtrlr"**: the component is `TariffCostCtrlr`. TC_I_105 lists
  ConditionsSupported = true although its name says false: the mock reports true and answers ConditionNotSupported.
- **TC_I_122**: `costDetails.totalCost.total` and `totalUsage` are mandatory in the schema but absent from the text:
  the test sends the fixed fee as total, and 12 Wh / 15 s as usage.
- **Block J has no tool validations**: a test passes when the CSMS answers every message. The meter values come from
  a small meter model (`metering.py`), with real sample times and real OCMF signatures.

### K: smart charging

- **TC_K_02**: the TxProfile without a transaction has no transactionId, as 2.0.1, although K01.FR.03 wants one.
- **TC_K_05, TC_K_32** "<Received chargingProfileId>": the id is one the mock station reports first (K_05: 5005), or
  the configured id (K_32).
- **TC_K_109** (errata flow) sends `call/SetChargingProfile` without an id; the CSMS chooses it.
- **TC_K_58, K_59, K_113** (renegotiation by the CSMS): the new TxProfile has the id of the transaction's current
  TxProfile (K01.FR.05, K01.FR.39).
- **TC_K_101 step 4** "TransactionEventResponse - status must be Accepted": the response has no status; the test
  requires a normal response.
- **TC_K_126** uses `provide-charging-profiles`, and turns it on again at its end.
- **ISO 15118-20 reusable states**: the mock reports `ISO15118Ctrlr.Enabled` and `V2XChargingCtrlr.Enabled` true.
  "Transaction just started" needs the OCSP mock on port 19080. The V2X AC_BPT state waits up to
  `CSMS_NO_ACTION_WAIT` for the charging profile that the CSMS may send after Accepted, and does not validate it.

### L, M: firmware and certificates

- **Block L**: `<Configured signingCertificate>` and `<Configured signature>` are generated per run (`firmware.py`)
  and given in the `call/UpdateFirmware` payload. Scheduled updates use now + 5 s.
- **Block M**: the configured certificates are `certs/ca.pem` (CSMSRootCertificate) and `certs/v2g_root_ca.pem`
  (V2GRootCertificate); the MO, Manufacturer and OEM roots are generated per run.
- **TC_M_20, TC_M_21**: the single Manual Action is two trigger calls: `call/GetInstalledCertificateIds`, then
  `call/DeleteCertificate` with the hash data that the station returned.
- **TC_M_100** needs the CPS interface to carry maximumContractCertificateChains and prioritizedEMAIDs to the CPS and
  remainingContracts back. `mock_cps_proxy.py` got an optional `contract_certificate_chains` for that.
- **TC_M_24, M_26, M_28** need the mocks on ports 19080 (OCSP) and 19081 (CPS), as in 2.0.1.

### N, O: diagnostics and display messages

- **TC_N_02 step 3** says `componentVariable[1]`: the test checks the only element, `[0]`.
- **TC_N_32** (clear, no report): the text still has a NotifyCustomerInformationRequest; it is sent with empty data.
- **TC_N_46** waits `CSMS_NO_ACTION_WAIT` for a SendLocalListRequest that the CSMS sends by itself, and triggers it
  otherwise.
- **TC_N_21, TC_N_24** "NotifyEventResponse with empty body": the payload must be exactly `{}`.
- **TC_N_105**: "CSMS does not respond to NotifyPeriodicEventStream" is checked for 1 s after each SEND. The test
  takes about 17 s, because it waits as the description notes.
- **Block O**: message content, ids and times come from the trigger payload (start now + 60 s, end now + 600 s).
  The optional "help" GetDisplayMessagesRequest of TC_O_04 is not used.

### P, Q, R, S

- **TC_P_03**: customData is `{vendorId, octtTestCase, sequence}`, on a Started / EVDetected TransactionEvent.
- **TC_Q_107** follows the errata flow (6.3.20). "Allow V2X after initial start" is
  `call/NotifyAllowedEnergyTransfer` with the charging-only mode and AC_BPT, so the test gives the allowed modes.
- **TC_Q_109, TC_Q_117**: the single Manual Action is two trigger calls: `call/SetChargingProfile`, then
  `update-dynamic-schedule`. TC_Q_117 uses 15 s, as its text says.
- **TC_Q_111** wants a setpoint in an ExternalSetpoint period that the CSMS sends: checked as printed.
- **TC_Q_124** uses the variable name `V2XLocalLoadBalancing` of the test text; the device model calls it
  `LocalLoadBalancing`.
- **TC_R_107** follows the errata (6.3.21) for steps 19-24. The control ids and settings come from the trigger
  payload. "Other optional fields must be omitted" is read as: the request has exactly isDefault, controlId,
  controlType and the one control object.
- **TC_S_103** follows the errata (6.3.22). The Ended events of the batteries that are taken out belong to
  transactions that the CSMS has not seen start.
