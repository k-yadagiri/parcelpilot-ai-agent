# Product Notes

## Scope decision: build both contexts, one codebase

The assessment allows building just one chatbot. I built both the
customer-facing and internal contexts from the same `UserContext` +
`build_tools()` foundation because the interesting product problem here is
less "can it answer a question" and more "does access control and source
trust hold up under two very different trust levels talking to the same
data" - that's easier to demonstrate convincingly with both sides visible
side by side than with one.

## Why the agent never trusts its own claim that a human confirmed something

The requirement is "any state-changing action must require explicit user
confirmation before it is executed." The weak version of this is a system
prompt that says "always ask before acting" - but a model can still be
talked into (or simply mistakenly) treating "yes go ahead" typed in chat as
sufficient and then calling the tool with some equivalent of "confirmed."
I treated confirmation as a UI-level authorization event, not a
conversational one: the only code path that writes to the database
(`execute_confirmed_action`) is wired to a real Streamlit button click, and
is not a tool the model can call. This means the worst a misbehaving or
confused model can do is *claim* something was created without it actually
happening - which is a wrong answer, not a data-integrity incident. I'd
rather have that failure mode than the reverse.

## Why service credits over ₹1,000 aren't blocked, just flagged

The SOP says credits over ₹1,000 require manager approval - it doesn't say
the AI can't propose them. I modeled this as: the tool records the credit
with `status = pending_manager_approval` when it should follow that path (a
real system would then route to a manager queue outside this tool's scope).
The alternative - refusing to create anything above the threshold - would
make the agent less useful for the actual approval workflow it's meant to
support.

## Why historical ticket resolutions are visible but explicitly distrusted

I could have simply hidden the `historical_resolution` field from the
tools. I chose to surface it (via `list_tickets`) but instruct the agent,
strongly, that it is context only and may be wrong, and to verify against
current documents before repeating it. Hiding it would remove a legitimate
signal ("this exact question came up before, here's what was said") that a
support agent - human or AI - benefits from seeing, as long as it isn't
treated as ground truth. The two seeded historical resolutions in the pack
are, deliberately, now-incorrect (they cite thresholds/limits that the
current SOP and product docs no longer state), which is a reasonable proxy
for what "the source base is intentionally imperfect" is testing for.

## Why the internal SQL tool is read-only and table-restricted

Giving staff arbitrary SQL power over a support system's database is a
realistic ops need (ad-hoc counts, cross-account patterns) but a real
security liability if ungated. Restricting it to `SELECT` against
`accounts`/`orders`/`tickets` - not `escalations`/`follow_up_tasks`/
`service_credits`, and never a write - keeps the tool useful for analysis
while keeping the state-changing tables reachable only through the
confirmed-action pattern.

## What I did not build, and why

- **Real authentication.** Explicitly permitted to mock; a real system
  would sit behind ParcelPilot's actual auth/session layer, and that layer
  - not this agent - would be the source of truth for `account_id`/role.
- **A production vector database.** See the architecture note - TF-IDF is
  the right tool for six documents; it would not be for six thousand.
- **Actually paging a human / creating a real ticket in an external
  system.** The action tools write to local tables, as the assessment
  explicitly allows ("The action tool may be mocked locally").
