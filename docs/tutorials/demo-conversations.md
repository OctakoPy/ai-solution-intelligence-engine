# Demo Conversations — plain English, verified transcripts

Four conversations you can run live, with **no technical knowledge needed**.
Every line below is the actual output of the running system, captured
verbatim, so you can check it against the screen before you present.

All wording is plain English on purpose. The user types like a normal person,
and ResolveIQ answers like a person.

Re-run them any time:

```bash
just api
uv run python scripts/demo_sweep.py
```

---

## Beat 1 — A plain question gets a plain answer

*Shows: it knows the answer and gives it, with proof.*

**YOU:** `I forgot my password and cannot log in to my computer`

**RESOLVEIQ:**
> According to the available documentation, the best answer is **Password
> reset request - forgot password**.
>
> **How to fix it**
> Reset password via self-service portal after identity verification, user
> regained access immediately.
>
> High confidence - this fix has worked every time it was tried.
>
> Track record: worked 45 of 45 times.

*Card shown: `TIC-1014` — Password reset request - forgot password*

No banner. It knew, so it answered.

---

## Beat 2 — Too vague, so it asks, then it answers

*Shows: it doesn't guess when it doesn't have enough, and it changes its
mind once you tell it more. This is the strongest beat in the demo.*

**YOU:** `finance user cannot open the report`

**RESOLVEIQ:**
> Not confident enough to recommend a fix. Confirm the error code, module,
> environment of the incident, then search again.

*Amber banner appears. Card shown: `TIC-1001` — User cannot access FI reports
in SAP - authorization error*

**YOU:** `error code S_RS_COMP, module SAP FICO, environment PROD`

**RESOLVEIQ:**
> According to the available documentation, the best answer is **User cannot
> access FI reports in SAP - authorization error**.
>
> **How to fix it**
> Checked user's role assignment in SU01. User was missing role
> Z_FI_REPORT_DISPLAY. Assigned role, ran SU53 to confirm, issue resolved
> after re-login.
>
> High confidence - this fix has worked every time it was tried.
>
> Track record: worked 8 of 8 times.

*Banner disappears. Same card, now answered.*

If asked what changed: the confidence moved from **0.45 to 0.73** because of
the three details you supplied. The card never changed — only the engine's
certainty about it.

---

## Beat 3 — The first fix did not work, so it finds another

*Shows: it is not a lookup box. It listens to the outcome and corrects itself.*

**YOU:** `my email is not arriving`

**RESOLVEIQ:**
> According to the available documentation, the best answer is **Cannot send
> emails with large attachments**.
>
> **How to fix it**
> This is expected behavior per company email size policy (20MB limit).
> Advised user to use SharePoint link sharing instead.
>
> High confidence - this fix has worked every time it was tried.
>
> Track record: worked 25 of 25 times.

**YOU:** `that did not work, still nothing`

**RESOLVEIQ:**
> According to the available documentation, the best answer is **Outlook not
> syncing new emails**.
>
> **How to fix it**
> Outlook was stuck in cached mode with a corrupted OST file. Rebuilt OST file,
> sync resumed normally.
>
> Good confidence - this fix has usually worked.
>
> Track record: worked 15 of 17 times.
>
> Ruling that out: Cannot send emails with large attachments. Here is the next
> best match instead.

*Card changes from `TIC-1019` to `TIC-1017`.*

This is the beat that answers the hardest question — *"how is this better than
a search box?"* Because it names what it threw out and why, and because the
second answer is the actually-correct one.

---

## Beat 4 — Nothing relevant, so it declines

*Shows: it says no instead of inventing an answer.*

**YOU:** `I ran out of milk in my house`

**RESOLVEIQ:**
> Nothing in the knowledge base matches this closely enough to recommend.
> Escalate to a subject-matter expert rather than applying a guess.

Also verified, same behaviour:

- `what is the weather in london`
- `where is a good place to get lunch`
- `how do i book a dentist appointment`

---

## Backup one-liners

If you need a quick answer to fill time, these all answer on the first turn:

| Type this | Gets |
| --- | --- |
| `I forgot my password and cannot log in to my computer` | Password reset, 45/45 |
| `a new starter needs a laptop for their first day` | Laptop setup standard, 40/40 |
| `something went wrong with a purchase order` | Goods receipt error, 6/6 |
| `the printer on my floor is not working` | Printer, asks for detail |
| `my laptop keeps disconnecting from the network` | Docking station, 13/13 |
| `I cannot open a spreadsheet that was sent to me` | Excel attachment, 11/11 |

## Questions you may be asked

**"How does it know?"**
It ranks every past record against the question, then shows the reasons it
picked one. Open **View Details** on any card — the "Why this" panel lists
them in plain English. **Show scoring detail** reveals the underlying numbers
for anyone who wants the method.

**"What if it's wrong?"**
Say so. *"That did not work"* is a first-class input — the engine drops that
record for the conversation and moves to the next one, naming what it ruled
out. The **Did this work?** buttons under each card record the same thing
permanently, and it changes future results for everyone.

**"Why does it sometimes ask me for more?"**
Because a confident wrong answer costs more than a question. It only answers
when the record matches the actual subject and has a track record that earned
trust — otherwise it asks or declines.

**"Does it replace our support team?"**
No. It removes the first hour of searching. Anything it is not sure about, it
hands to a person, and every outcome feeds back so the next answer is better.
