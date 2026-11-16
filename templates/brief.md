# Brief template

A brief is passed whole as the worker's first message. Fill every `<...>`. Delete lines that do not apply.
A real one: [examples/FLD-328/brief.md](../examples/FLD-328/brief.md). Why each part exists:
[docs/briefs.md](../docs/briefs.md).

```
You are the card-implementer for <App> card <ID>. The lead session is named "<lead-session>"; message it
with SendMessage (a deferred tool: load it with ToolSearch). Read the repo's CLAUDE.md first. Start from
current origin/<base-branch> (<commit> or later). Do not push or open a PR until the lead says so (a push
starts CI on the shared build machine).

Lane: <SIM-FREE: never boot a simulator or run xcodebuild; <who> holds the lane. Heavy builds only when
`uptime` load is under 30.>
   or <LANE HOLDER: you are the only simulator worker. Run the gate script before every boot. Be off the
   simulator, erased, during <nightly windows>.>

## <ID> (<priority>, <size>, <area>, <type>) <card title>
<The card text in full: what is wrong or wanted, with the evidence that opened the card (failing run, ids,
versions, picture paths). No guesses about the cause stated as fact.>

Done when:
- <a checkable item: a command and its expected result, or an observable state>
- <another; say what is explicitly out of scope and what to do with it>

Already decided by the owner: <decisions from the card notes, with dates; "none">
Already proven by earlier cards: <card ids and where their pictures are; "none">

## How to work
1. <method, not solution: what to read first, what to compare, what would count as proof>
2. <screens to capture and in which modes: light, dark, largest text size, device poses>
3. <which devices each new test must run on before hand-back>

## Rules
- Pictures go to ~/.claude/lead/handbacks/<ID>-shots/ right after each run.
- Each new test is shown failing on the old code. No fixed waits. No retries for a green.
- Print `git rev-parse HEAD` at the top of every log.
- Repo text says what the change does; findings and figures go in the hand-back.
- `git status` before every commit; one git command per call.
- Never wait by ending your turn; wait inside poll loops of 3 minutes or less.
- Message the lead at: <milestones>, blocked, and "<ID> ready for review".

Hand-back: ~/.claude/lead/handbacks/<ID>.md in the standard format, plus <anything card-specific>.
```
