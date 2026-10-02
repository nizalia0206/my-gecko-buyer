# The defence: Friday 2 October, six minutes

One design rule: everything you show ends in a **receipt** (it landed, and this is what
moved) or a **refusal** (it did not sign, and this is the field that disagreed).

## The six minutes

| Min | On screen | Backed by | What I say |
|---|---|---|---|
| 0:00 | your README's first lines: the sentence and the explorer link | `README.md` | This is a buyer agent for my store on Solana devnet. It pins what's asked before any bytes exist, and refuses by field when the prepared purchase disagrees. |
| 0:45 | your buyer reads the store menu live through Gecko, as part of the pin step | `uv run buyer --cases --recorded` output | My buyer reads the store menu live through Gecko's tools before anything is pinned — here's that step from a real run: dev3pack-cafe, 6 products, read through the store address on devnet. |
| 1:30 | the live buy: pin, prepare, 7 ticks, sign, verify, submit | `uv run buyer "one espresso" --devnet` | Watch it pin the ask to disk first, then prepare the purchase, check all seven fields against the pin, sign, verify, and submit — in that exact order, enforced by the runner, not by good intentions. |
| 2:30 | the landing: the explorer, then the receipt with ledger deltas | `receipts/<sig8>.md` | Here's the explorer link, and the receipt: buyer balance down, store balance up, total_purchases incremented by one. That's how I know it landed. |
| 3:15 | **the injected failure**: the judge draws a card; your buyer refuses and signs nothing | `buyer/check.py`, `refusals/` | Whichever card you draw, my buyer refuses by naming the exact field and both values it compared — nothing gets signed. |
| 4:30 | tests and the five-case table; one test that was red first | `uv run pytest`, `docs/EVAL_REPORT.md` | All six cases and four cards pass offline. The product check was the one that was wrong first — it matched on any shared word, so "one general-admission ticket" matched the VIP ticket on the menu. Fixed by requiring the full product name to appear in the ask. |
| 5:15 | the ADR: the decision, and what would reverse it | `docs/adr/0001-refusals-before-signing.md` | I decided to refuse before signing on any of seven fields, never retry a refusal unchanged. I'd drop the local price and mint checks if Gecko's own verify started binding them with the same guarantee — right now it doesn't, so I keep them. |

Everyone stays on devnet unless named a mainnet finalist.

**If the network or Gecko is down on stage,** switch to the recorded answers and say so:
`GECKO_SOURCE=recorded uv run buyer "one espresso" --devnet`. Same code path, replayed.

## The four cards

| Card | What the judge does | The command | The expected refusal |
|---|---|---|---|
| **Quantity** | asks for two espressos | `uv run buyer "two espressos" --devnet` | `quantity`: asked 2, prepared 1 |
| **Budget** | sets the budget to half the price | `uv run buyer "one espresso" --budget-raw <half> --devnet` | `price_raw`: both numbers |
| **Tampered bytes** | changes one byte of the signed transaction before verify | `uv run buyer "one espresso" --devnet --card tampered` | `signed bytes`: verify refuses, no submit |
| **Stale bytes** | waits past `expires`, then asks you to sign | `uv run buyer "one espresso" --devnet --card stale` | `blockhash`: bytes expired; prepare again, never re-sign |

Rehearsed offline, all 4/4: `uv run buyer --cards --recorded`.

## The seven questions

**The evidence**

1. **How do you know it landed?** The receipt reads the ledger twice — before and after —
   and shows the deltas plus `total_purchases` going from n to n+1, with the explorer link.
2. **What does your receipt not prove?** It proves what moved, not that I asked for the
   right thing. Today's real example: my product matcher briefly let a wrong product
   through before the price check happened to catch it — see docs/ISSUES.md.
3. **How does the chat know the refusal was right?** It names one field and both values,
   written to `refusals/<stamp>-<field>.json`, so it's checkable, not just trusted.

**The design**

4. **Why does Gecko never hold your key?** The key lives only in `buyer/signer.py`; Gecko
   only prepares unsigned bytes and verifies what I already signed. If Gecko held the key,
   it could sign a purchase without my agreement at all.
5. **Which check would you drop first?** Destination, if I ever trusted Gecko's own binding
   fully — but right now dropping it risks money landing in an account that isn't actually
   the store's own token account, even if product, price and mint all agree.
6. **What would reverse your ADR?** If Gecko's verify began binding price and mint with the
   same guarantee my local checks give, shown in its `binding_strength` field — then my
   local price and mint checks become duplicate work, and I'd drop them.
7. **What breaks it?** My product matching is a substring check against the exact pinned
   name — honest but literal. A rewording that doesn't contain any menu item's full name
   falls back to the raw ask text, which correctly refuses, but it means the parser itself
   has no real understanding of intent, only string matching.

## Before you go on stage

- [ ] One devnet receipt committed — pending funding
- [x] `uv run buyer --cases --recorded` → 6/6
- [x] `uv run buyer --cards --recorded` → 4/4
- [x] `uv run pytest` → 73 passed (core buyer logic); `scan_secrets.py` → clean, 93 files
- [ ] Buyer holds SOL and token — pending funding
- [x] Connector tried today — menu read live through Gecko, confirmed in every --cases run