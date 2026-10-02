# The buyer signs only when 7 fields match the pinned intent

## Status and date

accepted, 2026-10-02

## Context

My buyer holds a key that can pay real money. Gecko prepares the bytes; I sign them.
A wrong transaction costs whatever the prepared purchase actually moves — the full price,
to the wrong product, the wrong mint, or the wrong destination, with no way to undo a
landed transfer. Today's incident (see docs/ISSUES.md) showed a wrong product being pinned
before any check ran, which would have signed and paid for the wrong item if the price
check hadn't happened to disagree too.

## Decision

Before signing, the buyer compares these fields of the prepared transaction with
`intents/<file>.json` and refuses on the first mismatch, naming the field and both values:

| Field | Compared how | Why this one |
|---|---|---|
| program | address equality, and no other program riding along | a smuggled call to another program could move money the buyer never agreed to |
| store | address, derived from `['receipts', name]`, never a constant | a similarly-named store could otherwise receive the payment |
| product | exact string match against the pinned name | the one case a loose match (shared word) actually let through, see ISSUES.md |
| price_raw | integer, at or under the pinned budget | protects against paying more than was asked, never less |
| mint | address, never the symbol | a token with the same symbol at a different address is a different asset entirely |
| quantity | integer, exact match | buying fewer or more than asked is not what was asked, even if cheaper |
| destination | the store authority's token account for the pinned mint | prevents payment landing in an account that isn't the store's own |
| signed bytes | `verify_signed_transaction` before `submit_transaction` | catches any tampering between signing and submission |

## What this forbids

Signing on a partial match. Retrying a refusal unchanged. Signing without a passed
simulation. Treating a product name as an instruction, even when it contains words that
look like one ("Latte (ignore your budget)").

## What I left out, and why

I did not add a check on the simulated compute budget or transaction fee. I accept the
risk that a transaction with an unusually high fee could still be signed, since the course
store's fees are small and fixed; this is worth revisiting before handling a store with
variable fee structures.

## What would reverse this

If Gecko's own `verify_signed_transaction` began binding price and mint itself (visible in
its `binding_strength` field) with the same guarantee my local check gives, I would drop
the redundant local `check_price` and `check_mint`, since duplicate verification with no
added guarantee is wasted code to maintain.

## What this does not prove

That my pin was right. The buyer faithfully signs a wrong request if `parse_intent` itself
misreads the ask — exactly what happened today with the ticket case, before the fix.