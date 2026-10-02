# Issues

## 2026-10-02: check_product matched on any shared word, letting a wrong product through

- **What I saw:** case 2 ("one general-admission ticket") passed the product check and
  was refused on `price_raw` instead: `REFUSED on price_raw: asked 2000000, prepared 4000000`,
  when the fixture expected a refusal on `product`.
- **What was actually wrong:** `_find_product` in `buyer/intent.py` matched the ask against
  any product whose name shared one word with it. "Ticket" appears in both "general-admission
  ticket" and "VIP ticket", so it pinned the wrong product before the check ever ran.
- **How I found it:** read the trace line by line; the `pin` step already showed
  `1 x 'VIP ticket'`, so the wrong product was baked in before `check_product` could catch it.
- **What I changed:** `_find_product` now requires the full menu item name to appear in the
  ask, not just one shared word. A non-matching ask falls through to `check_product`, which
  then refuses correctly, naming both the asked and found product.
- **What it cost:** about 10 minutes, and no devnet SOL — caught entirely offline, on `--recorded`.
- **Would the checks have caught it?** Yes, eventually — `check_product` is correct. The
  bug was upstream, in what got pinned as the intent before any check ran. This is the
  risk of a greedy parser: a check can only compare against what it was given.

## 2026-10-02: verify_signed_transaction argument name mismatch broke every live purchase

- **What I saw:** `RecordedMiss: this fixture has no recorded answer for
  verify_signed_transaction:other`, even though the recorded fixture clearly had a
  `verify_signed_transaction` entry.
- **What was actually wrong:** I sent the signed bytes under the key `"signed_transaction"`,
  but the fixture's own matching logic compares `arguments.get("transaction")` against the
  recorded bytes. The wrong key meant it always fell through to the "other bytes" case.
- **How I found it:** read `buyer/mcp_client.py`'s `RecordedGecko.call`, which does the
  comparison explicitly and names the exact field it checks.
- **What I changed:** renamed the key from `signed_transaction` to `transaction` in
  `verify()`.
- **What it cost:** about 5 minutes, caught offline before any live attempt.
- **Would the checks have caught it?** No — this was an argument-naming bug between my
  code and Gecko's interface, not a field disagreement my seven checks are built to catch.