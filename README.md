# OCPP CSMS Test Suite

Python (`pytest`) implementation of OCTT scenarios for CSMS (Central System Management System) verification against OCPP 2.0.1 and OCPP 1.6J, with experimental (alpha) support for OCPP 2.1.

> **Need to test your CSMS?** Here's a [step-by-step setup guide](CSMS_SETUP.md). It covers TLS, the six
> test charging stations, the ID tokens, and the trigger API your CSMS has to provide, through to your first test run.

> **OCPP 2.1 support is experimental (alpha).** The 2.1 tests have only run against the bundled simulator, not
> against a real CSMS, and their trigger API and some of their interpretations may still change. See
> [OCPP 2.1 Support (Experimental)](#ocpp-21-support-experimental).

Based on:
- `OCPP 2.0.1 Specification, Edition 4 (2025-12-03)`
- `OCPP 1.6J Specification, (2025-11)`
- `OCPP 2.1 Specification, Edition 2, with the 2026-09 errata` (experimental)

## Project Structure

```
├── 2.0.1/                        # OCPP 2.0.1 test suite
│   ├── A/ … P/                   # Test blocks (sections A through P)
│   ├── reusable_states/          # Reusable states (shared preconditions)
│   ├── schema/                   # OCPP JSON schemas used by the tests
│   ├── conftest.py               # Pytest fixtures and shared setup
│   ├── trigger.py                # Trigger API client (CSMS-initiated actions)
│   ├── csms.py                   # Minimal in-memory CSMS for validating the tests
│   └── config.json               # Configuration of csms.py
├── 2.1/                          # OCPP 2.1 test suite (experimental)
│   ├── A/ … S/                   # Test blocks (sections A through S)
│   ├── reusable_states/          # Reusable states (shared preconditions)
│   ├── charge_point.py           # Mock charge point (2.1)
│   ├── ocpp_messages.py          # OCPP-J 2.1 message and schema helpers
│   ├── conftest.py               # Pytest fixtures and shared setup
│   ├── trigger.py                # Trigger API client (CSMS-initiated actions)
│   ├── smart_charging.py, …      # Helpers per topic (tariffs, firmware, certificates, …)
│   ├── csms.py                   # Minimal in-memory CSMS for validating the tests
│   ├── config.json               # Configuration of csms.py
│   ├── ERRATA.md                 # Impact of the 2026-09 errata on the tests
│   └── OPEN_QUESTIONS.md         # Open questions and decisions of the 2.1 tests
├── 1.6/                          # OCPP 1.6J test suite
│   ├── test_tc_*.py              # Test cases (TC_001 – TC_088)
│   ├── charge_point.py           # Mock charge point (1.6J)
│   ├── conftest.py               # Pytest fixtures and shared setup
│   ├── reusable_state_*.py       # Reusable states
│   └── trigger.py                # Trigger API client
├── certs/                        # Test certificates and keys (see certs/README.md)
├── tzi_charge_point.py           # Mock charge point (2.0.1)
├── utils.py                      # Shared helpers (TLS, auth, ids, timestamps, schemas)
├── contract_pki.py               # ISO 15118 test certificate chain helpers
├── mock_ocsp_responder.py        # Mock OCSP responder (the Test System's OCSP service)
├── mock_cps_proxy.py             # Mock CPS proxy (TC_M_26, TC_M_28)
├── generate_certs.sh             # Regenerates all test certificates
├── generate_contract_certs.sh    # Regenerates the ISO 15118 certificate chain
├── requirements_definitions.json # OCPP 2.0.1 requirement definitions (reference data)
├── CSMS_SETUP.md                 # Setup guide: testing your CSMS
├── DEBUGGING.md                  # Debugging OCPP traffic with --log-messages
├── pytest.ini                    # Test settings (defaults) and pytest options
└── requirements.txt              # Python dependencies
```

## Implemented Coverage

### OCPP 2.0.1

- `A` Security: 14
- `B` Provisioning: 22
- `C` Authorization: 16
- `D` Local Authorization List Management: 6
- `E` Transactions: 27
- `F` Remote Control: 15
- `G` Availability: 10
- `H` Reservation: 9
- `I` Tariff and Cost: 2
- `J` Meter Values: 9
- `K` Smart Charging: 32
- `L` Firmware Management: 19
- `M` Certificate Management: 18
- `N` Diagnostics: 30
- `O` Display Message: 21
- `P` Data Transfer: 2

**OCPP 2.0.1 total: 252 tests**

### OCPP 1.6J

75 test cases covering core charging station operations, authorization, transactions, smart charging, firmware management, and certificate handling.

**OCPP 1.6J total: 75 tests**

**Combined total: 327 tests**

### OCPP 2.1 (experimental)

- `A` Security: 15
- `B` Provisioning: 27
- `C` Authorization: 29
- `D` Local Authorization List Management: 6
- `E` Transactions: 36
- `F` Remote Control: 16
- `G` Availability: 10
- `H` Reservation: 9
- `I` Tariff and Cost: 12
- `J` Meter Values: 9
- `K` Smart Charging: 45
- `L` Firmware Management: 19
- `M` Certificate Management: 20
- `N` Diagnostics: 36
- `O` Display Message: 23
- `P` Data Transfer: 2
- `Q` Bidirectional Power Transfer: 13
- `R` DER Control: 2
- `S` Battery Swapping: 2

**OCPP 2.1 total: 331 tests (alpha, not counted in the combined total)**

One of them, TC_Q_102, is skipped: the 2026-09 errata removed the test case.

## Test Artifacts

- OCPP 2.0.1 and OCPP 2.1 test files follow `test_tc_<section>_<id>_csms.py` naming (e.g., `test_tc_k_01_csms.py`).
- OCPP 1.6J test files follow `test_tc_<number>_csms.py` naming (e.g., `test_tc_001_csms.py`).
- Every test file starts with its test description: the scenario steps and tool validations of the OCTT test case.
- OCPP 2.1 test descriptions also carry the errata entries that apply to them. `2.1/ERRATA.md` lists the impact of
  the 2026-09 errata on the tests.
- Mermaid sequence diagrams are included for all tests.
- Reusable states are in `2.0.1/reusable_states/`, `2.1/reusable_states/` and `1.6/reusable_state_*.py`, to keep
  setup consistent.

## Testing your CSMS

The [setup guide](CSMS_SETUP.md) walks through each step. In short, your CSMS needs:

1. **TLS on its WebSocket endpoint.** Every test connects over `wss://`, security profile 1 included. The CSMS needs an
   EC and an RSA server certificate for `localhost` issued by `certs/ca.pem`, and must trust `certs/ca.pem` for client
   certificates.
2. **Six registered charging stations.** For OCPP 2.0.1: `CP201_SP1` (security profile 1), `CP202_SP2` (profile 2) and
   `CP202_SP3` (profile 3). For OCPP 1.6J: `CP16_SP1` (profile 1), `CP16_SP2` (profile 2) and `CP16_SP3` (profile 3).
   The Basic Auth password is `test1234`.
3. **ID tokens** with the statuses the tests expect: Accepted, Invalid, Blocked, Expired, a master pass and its group,
   and an eMAID.
4. **An energy-based tariff** for block I.
5. **ISO 15118 trust.** `certs/v2g_root_ca.pem` is the root for contract certificates, and the CSMS must reach the
   mock services on `localhost` ports 19080–19082.
6. **The trigger API** ([below](#csms-trigger-api)).

Every setting has a default in `pytest.ini`, and an environment variable of the same name overrides it: for example
`CSMS_ADDRESS`, `CSMS_TRIGGER_ADDRESS`, or the station IDs. The setup guide's
[settings reference](CSMS_SETUP.md#reference-all-settings) lists them all.

The setup guide covers OCPP 2.0.1 and OCPP 1.6J. For OCPP 2.1, see
[OCPP 2.1 Support (Experimental)](#ocpp-21-support-experimental).

## CSMS Trigger API

Many OCTT test scenarios require CSMS-initiated actions (e.g., RequestStartTransaction, Reset, SetChargingProfile). The
official test case documents mark these as Manual Actions: a person has to make the CSMS send the request. To automate
this, the tests call an **HTTP trigger API that your CSMS has to provide**. 179 of the 252 OCPP 2.0.1 test files and 58
of the 75 OCPP 1.6J test files use it.

The tests call it through helper modules:

- `2.0.1/trigger.py`: `send_call()`, `trigger_v201()`, `get_variables()`, `set_variables()`, `reset()`, etc.
- `1.6/trigger.py`: `trigger_v16()`, `set_basic_auth_password()`, `create_token()`
- `2.1/trigger.py` (experimental): `send_call()`, `trigger_v21()`, `trigger_message()`, `get_variables()`,
  `set_variables()`, `set_transaction_limit()`, etc.

### API Convention

Every endpoint is a `POST` with a JSON body under `CSMS_TRIGGER_ADDRESS` (default `http://localhost:5001`). The CSMS
answers with HTTP 200 and a JSON body.

| Endpoint | Body | What your CSMS does |
|---|---|---|
| `/api/octt/2.0.1/{stationId}/call/{Action}` | The OCPP 2.0.1 request payload | Sends that CALL to the station, e.g. `call/RequestStartTransaction` |
| `/api/octt/2.0.1/{stationId}/{endpoint}` | Depends on the endpoint | Control endpoints: `trigger-message`, `update-basic-auth-password`, `get-variables`, `set-variables`, `clear-variable-monitoring`, `set-items-per-message`, `set-pending-boot`, `set-security-profile` |
| `/api/octt/1.6/{stationId}/{action}` | The OCPP 1.6 request payload | Sends the matching CALL. Actions are kebab-case, e.g. `remote-start-transaction` |
| `/api/octt/set-basic-auth-password` | `{"station_id": "...", "password": "..."}` | Stores a new Basic Auth password for the station |
| `/api/octt/create-token` | `{"token_id": "...", "status": "..."}` | Creates or updates an ID token with that status (Blocked or Expired) |
| `/api/octt/2.1/{stationId}/call/{Action}` (experimental) | The OCPP 2.1 request payload | Sends that CALL to the station, e.g. `call/SetDefaultTariff` |
| `/api/octt/2.1/…` (experimental) | Depends on the endpoint | Control endpoints of the OCPP 2.1 tests: those of 2.0.1 except `set-items-per-message`, and eight new ones |

Step 7 of the setup guide has [the full contract](CSMS_SETUP.md#step-7--implement-the-trigger-api): every
action, and the body and behavior of each control endpoint. tzi-csms, for example, provides the API when it is built
with `--features octt-triggers`. The setup guide does not cover the OCPP 2.1 endpoints yet; their contract is in
part 2 of [2.1/OPEN_QUESTIONS.md](2.1/OPEN_QUESTIONS.md), and it may still change.

## OCPP 2.1 Support (Experimental)

The OCPP 2.1 suite in `2.1/` is **alpha**. It implements the 331 CSMS test cases of blocks A–S from the official test
case descriptions and the 2026-09 errata. Before you rely on it, know that:

- **The tests have only run against the bundled simulator**, [2.1/csms.py](2.1/csms.py), which was written together
  with them. No real CSMS has run them yet, so some of them may be wrong.
- **Some interpretations are open.** Where a test description is ambiguous, or disagrees with itself or with the
  specification, the test makes a choice. [2.1/OPEN_QUESTIONS.md](2.1/OPEN_QUESTIONS.md) lists these choices, and
  they may change.
- **The trigger API of the 2.1 tests may change.** It has eight endpoints that the 2.0.1 API does not have.
- **The [setup guide](CSMS_SETUP.md) does not cover OCPP 2.1 yet.**

There is no complete list yet of what a CSMS needs for the 2.1 tests. The starting points are:

1. **A WebSocket endpoint for the `ocpp2.1` subprotocol**, over TLS as in step 2 of the setup guide.
2. **Three registered charging stations:** `CP21_SP1` (security profile 1), `CP21_SP2` (profile 2) and `CP21_SP3`
   (profile 3). The Basic Auth password is `test1234`.
3. **The trigger API under `/api/octt/2.1/…`.** It follows the conventions of the 2.0.1 API. The tests send 49
   actions through `call/{Action}`, 13 of which are new in OCPP 2.1, and use the control endpoints.
   [2.1/OPEN_QUESTIONS.md](2.1/OPEN_QUESTIONS.md) has the contract in part 2, and `2.1/trigger.py` is the client.
4. **The settings in `pytest.ini`.** Part 3 of the same file lists the ones that the 2.1 tests added, such as the
   prepaid cards, the VAT numbers and the QR code payment settings.

The OCPP 2.1 JSON schemas come from the `ocpp` package (`requirements.txt`), so `2.1/` has no `schema/` directory.
[Running Tests](#running-tests) and [CSMS Simulator](#csms-simulator) have the 2.1 commands.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the tests from the repository root, because the certificate paths in `pytest.ini` are relative to it.

## Running Tests

### OCPP 2.0.1

Run one or more blocks:

```bash
pytest -v -p no:warnings ./2.0.1/A ./2.0.1/B ./2.0.1/C
```

Run a specific test:

```bash
pytest -v -p no:warnings ./2.0.1/K/test_tc_k_01_csms.py
```

Run a specific test, logging OCPP bidirectional messages:

```bash
pytest -v -p no:warnings ./2.0.1/K/test_tc_k_01_csms.py --log-messages
```

[Debugging](#debugging) explains the output, and how to save it or use it without a terminal, for example in CI.

Run full 2.0.1 suite:

```bash
pytest -v -p no:warnings ./2.0.1
```

### OCPP 1.6J

Run the 1.6J suite:

```bash
pytest -v -p no:warnings ./1.6
```

Run a specific 1.6J test:

```bash
pytest -v -p no:warnings ./1.6/test_tc_001_csms.py
```

### OCPP 2.1 (experimental)

Run a block, a specific test with its OCPP messages logged ([Debugging](#debugging)), or the full 2.1 suite:

```bash
pytest -v -p no:warnings ./2.1/K
pytest -v -p no:warnings ./2.1/K/test_tc_k_01_csms.py --log-messages
pytest -v -p no:warnings ./2.1
```

So far these tests have only run against the [OCPP 2.1 simulator](#ocpp-21-simulator-experimental). TC_E_107 takes
two minutes: its transaction has a time limit of 120 seconds, and the test waits until it is reached.

### All Tests

The suites have modules with the same names (`trigger.py`, `conftest.py`), so run each in its own pytest session:

```bash
pytest -v -p no:warnings ./2.0.1 && pytest -v -p no:warnings ./1.6
pytest -v -p no:warnings ./2.1        # experimental
```

Collect-only (fast sanity check), per suite:

```bash
pytest --collect-only -q ./2.0.1
pytest --collect-only -q ./1.6
pytest --collect-only -q ./2.1
```

Some tests change a station's configuration in the CSMS: its Basic Auth password or its security profile. Restore the
stations before a rerun ([setup guide, step 10](CSMS_SETUP.md#step-10--reset-the-stations-before-a-rerun)).

## Debugging

When a test fails, run it alone with `--log-messages`. It prints every OCPP message between the test's charging station
and your CSMS, in both directions, with its payload:

```text
CSMS >>> [CALL] Reset (id=2ceb5d3f-009f-4f30-a49d-d3018b2267b4)
{
  "type": "OnIdle"
}

CP  >>> [CALL_RESULT] (id=2ceb5d3f-009f-4f30-a49d-d3018b2267b4)
{
  "status": "Accepted"
}
```

[DEBUGGING.md](DEBUGGING.md) explains how to read the trace next to the test description, what it does not show, how
to get from a failure to its cause, and how to save the trace or use it without a terminal (CI).

## OCSP Responder Validation

Several tests verify that the CSMS correctly validates certificate status via OCSP (RFC 6960). In these scenarios the Charging Station sends an `AuthorizeRequest` or `GetCertificateStatusRequest` that includes certificate hash data and/or a `responderURL`. The CSMS is then expected to connect to that URL, POST an OCSP request, and use the response to decide whether the certificate is valid or revoked.

Since there is no real CA or OCSP infrastructure in the test environment, the tests use a **configured (V2G) certificate chain** and a **local mock OCSP responder** that acts as the OCSP service of the Test System, as in the official test cases.

- **The chain.** `certs/v2g_root_ca.pem` -> `certs/contract_sub_ca.pem` -> `certs/contract_leaf.pem`, all ECDSA P-256. The contract certificate's CN is the configured eMAID (`EMAID001`). It is generated by `generate_contract_certs.sh` (also run by `generate_certs.sh`), and `contract_pki.py` loads it and computes OCSP request data from it.
- **The responder.** `mock_ocsp_responder.py` is spawned before the scenario and torn down afterward. It reads the CertID of each request and answers like a CA's responder (RFC 6960):
  - The answer is about exactly that certificate (`good`, `revoked` or `unknown`) and is current.
  - It is signed by the CA that issued the certificate. For a sub-CA, the response carries the sub-CA certificate.
  - A request about an unknown issuer is refused (`unauthorized`).
  - Every request is recorded, so a test can check what the CSMS asked about.

### CSMS configuration

A CSMS that verifies OCSP answers (C07.FR.05; RFC 6960 §3.2) must trust the root CA of the chain. The official TC_C_52 prerequisite is "signed by the configured V2GRoot or MORoot certificate at the CSMS". For tzi-csms:

```bash
CONTRACT_CERTIFICATE_TRUSTED_CA_PEM_PATH=../tzi-OCTT/certs/v2g_root_ca.pem
```

Without it, a CSMS cannot verify the chain and answers `CertChainError` (C07.FR.17). TC_M_24 does not need it: the CSMS passes the OCSP response on to the Charging Station.

### How it works

1. **Test starts** the mock responder on a dedicated port.
2. **CS sends** an OCPP request to the CSMS containing either:
   - `iso15118CertificateHashData` with the hashes of the configured chain (contract certificate and sub-CA) and a `responderURL` pointing to the mock (TC_C_50, TC_C_51), or
   - The contract certificate chain in PEM, whose AIA extensions name the mock's URL (TC_C_52), or
   - `ocspRequestData` with the hashes of the chain's sub-CA and a `responderURL` (TC_M_24).
3. **CSMS connects** to the `responderURL`, builds an RFC 6960 OCSP request, and POSTs it.
4. **Mock responder** answers about the requested certificate, signed by its issuing CA.
5. **Test asserts** two things:
   - the CSMS asked about certificates of the chain (the official "Test System checks that received request … is valid");
   - the CSMS returned the correct authorization/certificate status.

### Tests using the mock OCSP responder

| Test | Block | Port | certStatus | Scenario |
|------|-------|------|------------|----------|
| TC_C_50 | C (Authorization) | 19080 | `good` | CS provides hash data + responderURL; CSMS accepts valid certificate |
| TC_C_51 | C (Authorization) | 19081 | `revoked` (contract certificate) | CS provides hash data + responderURL; CSMS rejects revoked certificate |
| TC_C_52 | C (Authorization) | 19082 | `good` | CS provides the certificate chain (AIA extensions have the OCSP URL); CSMS verifies the chain, computes hashes, queries OCSP, accepts |
| TC_M_24 | M (Certificate Mgmt) | 19080 | `good` | CS sends `GetCertificateStatusRequest`; CSMS queries OCSP and returns `ocspResult` |

### Network requirements

The CSMS under test must be able to reach `localhost` on ports **19080–19082** (HTTP). If the CSMS runs in a container
or on a remote host, ensure these ports are forwarded or accessible. No TLS is used for the OCSP endpoint — the mock
serves plain HTTP only. Port 19081 also serves the mock CPS proxy (`mock_cps_proxy.py`) in TC_M_26 and TC_M_28 (setup
guide, step 6).

## CSMS Simulator

[csms.py](2.0.1/csms.py) is a minimal in-memory CSMS for checking the behavior of the tests themselves. You don't need
it to test your own CSMS, and it is not intended for production use. It supports OCPP 2.0.1 only, so the 1.6J suite
cannot run against it. The OCPP 2.1 suite has [its own simulator](#ocpp-21-simulator-experimental).

### Running it

Its ports are the test defaults in `pytest.ini`. Start it, with the virtual environment active:

```bash
python 2.0.1/csms.py
```

It is ready when it logs `CSMS 2.0.1 simulator started.` In another terminal, run the 2.0.1 tests as usual, for
example:

```bash
pytest -v -p no:warnings ./2.0.1/B/test_tc_b_20_csms.py
```

| Server | Port in `config.json` | Used by the tests |
|---|---|---|
| WSS: TLS, with Basic Auth or a client certificate | `CSMS_WSS_PORT`: 9000 | Yes, as `CSMS_ADDRESS` (`wss://localhost:9000`) |
| WS: Basic Auth without TLS | `CSMS_WS_PORT`: 8082 | No |
| Trigger API (HTTP) | `CSMS_TRIGGER_PORT`: 5001 when not set | Yes, as `CSMS_TRIGGER_ADDRESS` (`http://localhost:5001`) |

To run it next to another CSMS, give it other ports in `config.json` and point the tests at them, for example
`CSMS_ADDRESS=wss://localhost:9100 CSMS_TRIGGER_ADDRESS=http://localhost:5101 pytest …`.

- **Stations:** it accepts any station ID with the password `BASIC_AUTH_CP_PASSWORD` (`test1234`). The stations in
  `CSMS_SP3_STATION_IDS` connect with a client certificate (security profile 3).
- **Trigger API:** it has no `create-token` (only the 1.6J tests use it) and no `clear-variable-monitoring`, so
  TC_N_18 fails against it.
- **Test modes (optional):** a test mode makes it perform an action by itself when a station connects. The tests do
  not need them, because they trigger these actions through the trigger API. Set one with
  `python 2.0.1/csms.py <test_mode>`, or with `CSMS_TEST_MODE` or `CSMS_CP_ACTIONS` in `config.json`. The docstring
  of [csms.py](2.0.1/csms.py) lists the modes.

### Configuration

All settings come from `2.0.1/config.json`; the simulator reads no environment variables. Key fields:

- `CSMS_WSS_PORT`, `CSMS_WS_PORT`, `CSMS_TRIGGER_PORT` (optional, default 5001)
- `BASIC_AUTH_CP`, `BASIC_AUTH_CP_F`, `BASIC_AUTH_CP_PASSWORD`, `CSMS_SP3_STATION_IDS`
- `CONFIGURED_EVSE_ID`, `CONFIGURED_CONNECTOR_ID`, `CONFIGURED_CONNECTOR_TYPE`, `CONFIGURED_NUMBER_OF_EVSES`
- `VALID_ID_TOKEN`, `VALID_ID_TOKEN_TYPE`, `GROUP_ID`, `MASTERPASS_GROUP_ID`
- `CSMS_SERVER_CERT`, `CSMS_SERVER_KEY`, `CSMS_SERVER_RSA_CERT`, `CSMS_SERVER_RSA_KEY`, `CSMS_CA_CERT`, `CSMS_CA_KEY`
- `CSMS_CP_ACTIONS`, `CSMS_TEST_MODE`

To set up your own CSMS for the tests, follow the [setup guide](CSMS_SETUP.md).

### OCPP 2.1 simulator (experimental)

[2.1/csms.py](2.1/csms.py) is the same kind of simulator for the OCPP 2.1 suite: a minimal in-memory CSMS, not
intended for production use. So far it is the only CSMS that the 2.1 tests have run against. Start it, with the
virtual environment active:

```bash
python 2.1/csms.py
```

It is ready when it logs `CSMS 2.1 simulator started.` In another terminal, run the 2.1 tests, for example:

```bash
pytest -v -p no:warnings ./2.1/B/test_tc_b_20_csms.py
```

| Server | Port in `2.1/config.json` | Used by the tests |
|---|---|---|
| WSS: TLS, with Basic Auth or a client certificate | `CSMS_WSS_PORT`: 9000 | Yes, as `CSMS_ADDRESS` (`wss://localhost:9000`) |
| Trigger API (HTTP), which is also its log server over HTTP | `CSMS_TRIGGER_PORT`: 5001 | Yes, as `CSMS_TRIGGER_ADDRESS` (`http://localhost:5001`) |
| Log server over HTTPS | `CSMS_LOG_HTTPS_PORT`: 5002 | Yes, by TC_N_103 |

- **One simulator at a time:** its default ports are those of the 2.0.1 simulator.
- **Stations:** it accepts the stations in `STATIONS` of `2.1/config.json`, each with its security profile:
  `CP21_SP1`, `CP21_SP2` and `CP21_SP3`. It refuses any other station ID.
- **Configuration:** all settings come from `2.1/config.json`; it reads no environment variables. It stores nothing,
  so a restart resets it.


## Contributing

Contributions are welcome via pull requests.

## Authors

[tzi.app](https://www.tzi.app)

## License

[MIT](https://choosealicense.com/licenses/mit/)
