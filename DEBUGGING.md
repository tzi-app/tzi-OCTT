# Debugging OCPP traffic with `--log-messages`

When a test fails, pytest shows the check that failed: what the test expected. To see what actually went over the
wire, run the test with `--log-messages`. It prints every OCPP message between the test's charging station and your
CSMS, in both directions, with its full payload.

The commands below assume the virtual environment from the README's [Installation](README.md#installation) section is
active.

## Turn it on

Add `--log-messages` to the pytest command. Both suites support it and print the same format:

```bash
pytest -v -p no:warnings ./2.0.1/B/test_tc_b_20_csms.py --log-messages
pytest -v -p no:warnings ./1.6/test_tc_013_csms.py --log-messages
```

- **Debug one test file at a time.** The messages of all the tests in a run go into one trace.
- **The messages go straight to the terminal** (`/dev/tty`), between pytest's own lines, even while pytest captures
  output, so you don't need `-s`. It also means that `> file` does not capture them; see
  [Saving the trace, or running without a terminal](#saving-the-trace-or-running-without-a-terminal).

## Reading the trace

This is part of the trace of TC_B_20 (Reset Charging Station - Without ongoing transaction), run against tzi-csms:

```text
CSMS >>> [CALL] Reset (id=2ceb5d3f-009f-4f30-a49d-d3018b2267b4)
{
  "type": "OnIdle"
}

CP  >>> [CALL_RESULT] (id=2ceb5d3f-009f-4f30-a49d-d3018b2267b4)
{
  "status": "Accepted"
}

CP  >>> [CALL] BootNotification (id=80dd66c7-3ebb-4eb9-ae69-33eea72695b1)
{
  "chargingStation": {
    "model": "CP Model 1.0",
    "vendorName": "tzi.app"
  },
  "reason": "PowerUp"
}

CSMS >>> [CALL_RESULT] (id=80dd66c7-3ebb-4eb9-ae69-33eea72695b1)
{
  "currentTime": "2026-11-23T00:29:56.673Z",
  "interval": 60,
  "status": "Accepted"
}
```

Each message is a header line, then its JSON payload:

| Part | Meaning |
|---|---|
| `CP  >>>` | Sent by the test's charging station to your CSMS |
| `CSMS >>>` | Received from your CSMS |
| `[CALL] Reset` | A request, with its action |
| `[CALL_RESULT]` | The response to the request with the same id |
| `[CALL_ERROR] <code>: <description>` | An error response to the request with the same id |
| `(id=…)` | The OCPP message id. A response carries the id of the request it answers |

**Read the trace next to the test description** at the top of the test file. In TC_B_20:

| Test description | Trace |
|---|---|
| Manual Action: Request the CSMS to reboot the Charging Station with type OnIdle | Not in the trace. tzi-OCTT does it through the [trigger API](CSMS_SETUP.md#step-7--implement-the-trigger-api) |
| 1. The CSMS sends a ResetRequest. Validation: evseId must be omitted | `CSMS >>> [CALL] Reset`. Its payload has no `evseId` |
| 2. The OCTT responds with a ResetResponse with status Accepted | `CP  >>> [CALL_RESULT]` with the same id |
| 3. The OCTT sends a BootNotificationRequest | `CP  >>> [CALL] BootNotification` |
| 4. The CSMS responds with a BootNotificationResponse. Validation: status Accepted | `CSMS >>> [CALL_RESULT]` with the same id, `"status": "Accepted"` |

An error response looks like this. In TC_B_30 (Cold Boot Charging Station - Pending/Rejected - SecurityError), the
CSMS answers the boot with Pending or Rejected, and then has to refuse the station's other requests with a
SecurityError:

```text
CP  >>> [CALL] NotifyEvent (id=8d6e875c-2481-4f9c-ae4f-f84490f6a948)
{
  "generatedAt": "2026-11-23T02:30:12.782136Z",
  "seqNo": 1231230,
  "eventData": [ … ]
}

CSMS >>> [CALL_ERROR] SecurityError: Action not allowed in current registration state (id=8d6e875c-2481-4f9c-ae4f-f84490f6a948)
{}
```

(`eventData` shortened.)

## What the trace does not show

- **The trigger API calls.** Manual Actions reach your CSMS over HTTP (`CSMS_TRIGGER_ADDRESS`), not over OCPP. The
  trace shows their effect: the request your CSMS sends next.
- **The connection setup.** The TLS handshake and the WebSocket upgrade come before the first message. If your CSMS
  refuses the connection, the trace stays empty and pytest's error says why, for example
  `server rejected WebSocket connection: HTTP 401`.
- **Which connection a message belongs to.** The header does not name the station. In tests that reconnect, the
  messages of each connection follow each other in the one trace.

## From a failure to its cause

| What the trace shows | What it usually means |
|---|---|
| The test waits for a request from your CSMS, often right after a Manual Action, and no `CSMS >>> [CALL]` for it arrives | Your CSMS did not send it. Check the trigger endpoint ([setup guide, step 7](CSMS_SETUP.md#step-7--implement-the-trigger-api)) and your CSMS's logs |
| The request arrives, but the test fails on a check | Compare its payload with that step's tool validations in the test description |
| `CSMS >>> [CALL_ERROR]` in answer to the station | Your CSMS rejected the station's message. The code and description say why |
| `CP  >>> [CALL_ERROR]` in answer to your CSMS | The test station could not handle the request; `cause` in the payload says why. On a schema failure, `ocpp_message` shows the message that failed. If it is your CSMS's request (`[2, …]`), the request does not match the OCPP schema. If it is the station's own response (`[3, …]`), the problem is in tzi-OCTT |
| Nothing at all | The connection failed before the first message. See pytest's error and the setup guide's [troubleshooting](CSMS_SETUP.md#troubleshooting) |

Each message has an id. If your CSMS logs OCPP message ids, **search its log for the id** to see how it handled that
message.

## Saving the trace, or running without a terminal

The trace goes to `/dev/tty`, so:
- shell redirection (`> trace.log`) does not capture it;
- without a terminal, for example in CI, pytest cannot open `/dev/tty` and stops while collecting the tests:

  ```text
  E   OSError: [Errno 6] Device not configured: '/dev/tty'
  ```

  That is the macOS wording; Linux says `No such device or address`.

Run pytest under `script`, which gives it a terminal and records the session to a file:

```bash
# macOS
script -q trace.log pytest -v -p no:warnings ./2.0.1/B/test_tc_b_20_csms.py --log-messages

# Linux (util-linux). -e returns pytest's exit code
script -q -e -c "pytest -v -p no:warnings ./2.0.1/B/test_tc_b_20_csms.py --log-messages" trace.log
```

The file also holds pytest's output, with the terminal's colour codes. Read it with `less -R trace.log`, or strip the
codes:

```bash
perl -pe 's/\e\[[0-9;?]*[a-zA-Z]//g; s/\r//g' trace.log > trace.txt
```
