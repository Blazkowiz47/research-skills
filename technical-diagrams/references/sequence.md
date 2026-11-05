# Sequence diagrams

Use when the question concerns who calls whom and in what order. Read the actual
call sites and relevant callees for an existing codebase. Method names alone do
not establish call order, conditions, or synchronous/asynchronous behavior.

## Notation

- Objects/participants: pastel headers, with class or service names; add instance
  names when multiple instances matter. Time proceeds downward along lifelines.
- Synchronous calls: solid arrows labeled with the method and meaningful arguments.
- Returns: dashed arrows labeled with the result. Omit trivial returns when that
  helps readability, but retain returns needed to follow dependencies.
- Active execution: narrow activation bars, including nesting when relevant.
- Self-calls: loop back to the same lifeline. Do not invent another object merely
  to draw an internal helper.
- Async sends: visibly distinct labeled arrows; do not imply the sender waits.
  Show callback/event handling separately when the ordering matters.
- Branches and loops: framed `alt`, `opt`, or `loop` regions with explicit
  conditions. Mark exceptions, cancellation, and background work when relevant.

Vertical ordering shows logical sequence, not elapsed duration unless measured
timing is explicitly represented. Concurrent events need not have a total order.

## Modes

**Explain:** trace one concrete scenario, identifying entry point, inputs,
intermediate returns, and final result. Expand a confusing self-call in a separate
view only when needed. Include a failure branch if it answers the question.

**Present:** keep participants and messages essential to the interaction. Move
long signatures to accompanying prose while retaining exact method names where
they are the subject. Keep labels readable at final size.

## Reference example

- [Method-call preview](../assets/examples/sequence.png)
- [Editable SVG](../assets/examples/sequence.svg)

The example's method names are illustrative. It shows a synchronous payload-building
call, not the complete asynchronous indexing service or its storage commit.
