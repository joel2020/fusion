# Lenovo Autonomous Calling Workstation Design

## Objective

Configure Joel's Lenovo Yoga 7 as a dedicated calling workstation for 100 daily dial attempts. The system uses SpokePhone for calls, an ElevenLabs conversational agent named John, Outlook for live availability checks, Zoho Bookings for appointment creation, and Zoho CRM for lead management. No prospect calls begin until internal testing and a supervised pilot pass.

## Confirmed Environment

- Lenovo Yoga 7 model 83JT running Windows 11 Home
- Intel Core Ultra 5 226V and 16 GB RAM
- Spoke Phone 10.18.0 installed
- Chrome and Tailscale installed
- Working microphone, speaker, Bluetooth, and USB audio devices
- Secure SSH access over Tailscale, restricted to Joel's Mac
- Zoho CRM and Zoho Bookings sessions available in Chrome Profile 2
- Zoho CRM account can access Setup but is denied Developer Hub `APIs and SDKs`
- `Set First EOI Meeting` is a Zoho Blueprint transition

## Architecture

The workflow runs locally on the Lenovo to minimize audio and interface latency. SpokePhone remains the dialer. A Windows virtual-audio bridge connects SpokePhone audio to the ElevenLabs conversational agent. Chrome stays signed in to Outlook, Zoho Bookings, and Zoho CRM.

Zoho control is browser-first because Joel's account cannot use the CRM API. Automation targets named page elements and field labels rather than fixed screen coordinates. The next lead and calendar are preloaded while the current workflow completes.

Only one call may be active. A state controller coordinates lead selection, dialing, conversation, post-call updates, verification, retry, and pause states.

## Caller Identity and Conversation

- Agent name: John
- Voice: Joel's authorized ElevenLabs voice labeled `Joel`
- Required opening: `Hi [First Name], this is John, Joel's assistant with Fusion Growth Partners.`
- Live calls and voicemail must not claim that John is Joel.
- The words `virtual assistant` and `AI assistant` are not used in voicemail.
- The agent follows the approved cold-call script, using natural pacing, occasional fillers, and interruption handling.
- John must not invent facts, prices, production, reviews, availability, or qualifications.
- The lead's annual production comes from Zoho and is confirmed verbally.
- Corrected production, current production, growth goal, and qualification details are retained for the post-call qualification summary.
- An explicit do-not-call request ends solicitation immediately and suppresses future dialing using Fusion's existing suppression mechanism once that control is mapped in the supervised pilot.

## Lead Queue and Calling Windows

The daily target is 100 dial attempts. An immediate double dial counts as two attempts.

John opens Zoho CRM `Leads` and selects the qualified cold-calling view that corresponds to the lead's time zone:

- Eastern qualified leads for cold calling
- CT qualified leads for cold calling
- MT qualified leads for cold calling
- PT qualified leads for cold calling

Within a selected view, John applies `Notes` -> `Without` -> `30 days`.

Cold calls are placed only during these windows in the lead's local time:

- 9:00-11:00 a.m.
- 3:00-7:00 p.m.

The natural daily sequence is Eastern, Central, Mountain, then Pacific as their local windows open. Prospect-requested callbacks may occur outside these cold-calling windows at the exact requested time.

## Call Outcomes

### Unanswered

1. Place the first call.
2. If unanswered, redial immediately without adding a note.
3. If the second attempt is unanswered, leave the approved voicemail.
4. Add exactly one short note, normally `ddvm` or the matching established Zoho note style.

No third attempt is placed in the same sequence.

### Connected but No Meeting

John follows the approved script and objection handling. After the call, he adds exactly one short, natural note consistent with recent account notes.

### Callback Requested

John confirms the callback date, time, and time zone. After the call, he:

1. Changes the lead-status field from `Suspect` to `Prospect`; he does not use Zoho's formal Convert Lead action.
2. Changes the lead owner to `Joel Carias`.
3. Creates a callback task on the lead for the requested date and time.
4. Adds one short note.
5. Places the callback when the task becomes due, even if the requested time falls outside the standard cold-calling windows.

### EOI Agreed

During the call, John checks Joel's Outlook calendar and offers an open time Monday-Friday from 8:00 a.m. to 7:00 p.m. Eastern. Back-to-back appointments are allowed. John confirms the prospect's email address, phone number, date, time, and time zone, then closes with:

`Great - I'll send the calendar confirmation over shortly. I'll see you on [day] at [time and time zone].`

The administrative work happens immediately after the call.

## Post-Call EOI Booking

1. Recheck Outlook to ensure the agreed slot is still open.
2. In Zoho Bookings, choose `+` -> `Appointments`.
3. Choose workspace `Partnership, Executive, EOI meetings`.
4. Assign consultant `Joel Carias`.
5. Select the agreed date and time.
6. Under Customer, create a new customer from the Zoho CRM lead's name, email, and phone.
7. Add the appointment.
8. In Zoho CRM, change the lead status from `Suspect` to `Prospect` and the lead owner to `Joel Carias`.
9. Run the `Set First EOI Meeting` Blueprint transition with:
   - `EOI set by?`: `Joel Carias`
   - `EOI Set For`: `Joel Carias`
   - `EOI Scheduled Date`: agreed date and time
   - `Lead Time Zone`: prospect's time zone
   - `Lead Source`: `Cold Call`
10. Add the qualification summary, including confirmed or corrected production, growth goal, and other script-required qualification details.
11. Add one short, human-sounding call note.
12. Verify the appointment appears in Zoho Bookings and Outlook, and read the CRM record back to verify the transition and ownership.

John does not start another dial until all three systems agree. If Bookings succeeds but CRM fails, he retries the CRM step and pauses the queue if the mismatch remains.

## Daily Tasks and Reminders

At the start of the workday and between calling blocks, John reviews Joel's Zoho CRM tasks. Due callback tasks are completed at their requested times. Existing 15-minute and 10-minute reminder tasks trigger the approved prospect text workflow. Sending real texts is disabled until the exact templates, sender, and supervised test are approved.

## Notes

There is no separate call-disposition field. Every completed call sequence gets one note total. Notes mirror the account's established concise style. Examples include:

- `ddvm`
- `Spoke briefly - not interested.`
- `Callback requested for Aug 13 at 4 PM ET - task created.`
- `EOI set for Aug 14 at 10 AM ET.`

Zoho metadata supplies author and creation time, so notes do not duplicate those details.

## Safety and Failure Handling

- No prospect calls occur during setup, internal tests, or the initial dry run.
- First calls use approved internal/test numbers.
- The supervised pilot validates one example of every outcome before unattended operation.
- Missing production, phone, email, date, time, time zone, or required Blueprint fields pauses the affected workflow.
- Unexpected SpokePhone, audio, Outlook, Bookings, or CRM state pauses automation instead of guessing.
- John never books an ambiguous time or assumes a time zone.
- A slot is rechecked immediately before it is created.
- A successful write is verified by reading the resulting record or calendar entry.
- Duplicate-call and duplicate-booking guards use the lead ID, phone number, appointment time, and current workflow state.
- Secrets, browser cookies, passwords, and OAuth tokens are never copied out of their authorized applications.
- Current company policies and applicable federal and state calling requirements must be reviewed before unattended calling is enabled.

## Performance Targets

- Natural conversational latency, with interruption support
- Availability lookup during the call without extended silence
- Post-call Bookings and CRM completion typically within 5-10 seconds when Zoho responds normally
- Immediate double dial after the first unanswered attempt
- 100 dial attempts within the approved local-time windows

Performance is measured during the supervised pilot; estimates are not treated as guarantees.

## Acceptance Tests

The workstation is ready for a supervised pilot only when all of the following pass:

1. Two-way SpokePhone and ElevenLabs audio works without echo or feedback.
2. John states the approved identity and does not claim to be Joel.
3. Interruption handling and script branching work on an internal test call.
4. Lead selection respects the time-zone view, 30-day note filter, and local calling windows.
5. An unanswered internal test performs exactly two calls, leaves voicemail only on the second, and creates one note.
6. A callback test changes status and owner, creates the task, adds one note, and executes at the requested time.
7. An EOI test checks Outlook during the call and completes Bookings and CRM after hang-up using the required values.
8. Outlook, Bookings, and CRM verification detects a deliberately introduced mismatch.
9. A do-not-call test halts solicitation and prevents redial.
10. An unexpected page, missing field, audio failure, or authentication prompt pauses the workflow safely.

## Deployment Stages

1. Install and configure the local runtime and virtual audio bridge.
2. Build read-only lead, Outlook, Bookings, CRM, and task inspection.
3. Build internal-number dialing and conversation tests.
4. Build post-call CRM and Bookings writes in a controlled test record.
5. Run supervised outcome tests and confirm notes, fields, reminders, and recovery behavior.
6. Run a small supervised prospect pilot.
7. Enable unattended calling only after Joel approves the pilot evidence and compliance review.
