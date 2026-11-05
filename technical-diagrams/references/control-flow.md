# Control flow

Use for decisions, branches, loops, termination, failures, and retry policies.
For existing code, derive conditions and paths from the relevant implementation.

## Notation and completeness

- Actions: softly filled blocks with verbs.
- Decisions: diamonds with concise predicates. Label outgoing edges with their
  conditions; use yes/no only when the predicate makes those meanings clear.
- Start/end: make entry and terminal outcomes apparent. Distinguish success,
  failure, cancellation, and continuation into omitted processing as needed.
- Loops: route the back edge clearly to the repeated operation. Show the exit
  condition and relevant state updates rather than implying an unbounded retry.
- Retry: distinguish retryable from terminal failures, name the attempt/time
  limit, and state whether a limit counts retries or total attempts. Preserve
  backoff, cleanup, or rollback when they affect behavior.

Use labeled arrows and shape as well as color to distinguish paths. A failed
validation is not necessarily a transient error. Do not silently route every
failure back into a retry loop.

## Modes

**Explain:** show the main path and the exceptions needed to understand it. Make
state changes that control a loop visible in nodes or a concise annotation.

**Present:** keep conditions and exits that support the explanation; collapse
routine action sequences into named subprocesses. Do not omit a failure exit
in a way that falsely makes a retry or algorithm appear guaranteed to succeed.

## Reference example

- [Bounded retry preview](../assets/examples/control-flow.png)
- [Editable SVG](../assets/examples/control-flow.svg)

The example allows at most three total fetch attempts. Its policy is illustrative;
derive real limits and retry conditions from the system being explained.
