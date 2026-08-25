# Design review — 014

One round against the specification, the plan, the task list and the reconciliation, on 2026-08-25,
before any implementation. Nine findings, all verified against the code and all accepted. The plan,
the task list and the reconciliation were amended in place; this file records what changed and why,
so a later reader does not have to reconstruct it from the diff.

## Accepted and applied

**The registered pages disclose that a private dataset exists.** The pages being retired answer
not-found for a private record on purpose, matching the API. The registration path cannot: a refused
request goes to `PermissionRequiredMixin.handle_no_permission`, which redirects an anonymous visitor
to sign in and gives a signed-in stranger a permission refusal — both confirming the record is there.
Nothing in the plan mentioned it, and the only symptom would have been two assertions going red
inside an address sweep. Plan P1 now states the decision — the not-found response is preserved
through a `handle_no_permission` override — and T061a asserts it at all four addresses, with the
public-but-refused case tested separately so the two are not collapsed.

**A fourth filter is broken, not three.** `image` is inherited from the shared list filter, which
points at a relation neither record type has; applying it raises `FieldError` and the page fails.
Confirmed by running the filterset. The fix is one line in the shared base and repairs the project
listing too. T016 now requires the test to enumerate the filters the rendered form actually offers,
so it cannot be satisfied against a hand-written list.

**The order was unworkable.** An additional view has no route of its own — it is mounted inside the
owning registration's patterns. With the registration placed last, every page built in the three
preceding steps had no address, so each of their tests would have failed with an unresolvable name
rather than for the reason it states. The registration and the address move come first; the links and
the navigation-entry count stay where they were.

**Five tasks were ticked against tests of the pages this feature retires** — the update and deletion
refusals among them, which are the two that matter. The same situation two entries later was
correctly left open. All five moved to open, as built-differently.

**One task was ticked on a signed-out-only test** while both the task and its success criterion name
the signed-in cases. Moved to open.

**The listing offered two different searches** over different field sets, neither reaching the
dataset's external identifiers — the thing a researcher actually pastes into a search box. One search
now, over name, uuid, identifiers, descriptions and keywords.

**The expected-to-fail mark needed to be strict.** `xfail_strict` is not set in this project, so
without it the upstream deletion fix would land, the test would pass unexpectedly, and nothing would
report it — losing the only signal that the deletion page had become usable in a browser.

**The project filter's rule was named.** It is not the creation form's rule: that one is
contribution-based, which is right for "projects this researcher may file under" and raises on a
listing open to anonymous visitors.

**One reconciliation entry cited a test that does not exist yet** as present evidence. Re-pointed at
the open task that will enforce it.

## Consequences

Reconciliation totals move from 84 tasks, 25 satisfied, to 85 tasks, 19 satisfied. The six ticks
withdrawn were coverage assumed rather than coverage present.
