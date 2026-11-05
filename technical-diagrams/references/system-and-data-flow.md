# System & data flow

Default to one overview combining components with the data moving between them.
Adjust emphasis to infrastructure or transformations according to the question.

## Structure and flow

- Components: translucent cuboids or flat blocks with a concise responsibility.
- Boundaries: light labeled enclosures for processes, services, ownership,
  deployment, or trust. State which boundary is represented; do not conflate them.
- Connections: name the operation or payload, such as `enqueue(job_id)`,
  `document bytes`, `chunks`, or `embeddings`. State whether arrows represent
  interactions or actual data movement. A read request and its result travel
  in opposite directions.
- Transformations: show important processing steps inside the component that
  owns them. One worker may parse, chunk, and embed; three steps do not imply
  three independently deployed services.
- Stores and queues: distinguish durable state, buffered work, and computation.
  Show identifiers, schemas, or cardinality only where they explain the flow.

Keep source, transformation, and destination traceable. Preserve metadata joins,
filters, fan-out/fan-in, and material data losses. Do not infer concurrency,
delivery guarantees, or deployment topology from the appearance of a pipeline.

## Modes

**Explain:** give the combined overview first. Expand one component into a local
pipeline if its transformations would crowd the overview. Reuse its name/color
and show how the expanded view connects back.

**Present:** emphasize the boundaries and transformations relevant to the claim.
Remove incidental helpers, retain important stores and interfaces, and label
omitted processing. Split into panels when preserving meaning requires it.

## Reference examples

- [Structure emphasis preview](../assets/examples/system-architecture.png)
  and [SVG](../assets/examples/system-architecture.svg)
- [Transformation emphasis preview](../assets/examples/data-flow.png)
  and [SVG](../assets/examples/data-flow.svg)

These accepted examples illustrate the two emphases within this single type;
they do not require producing two diagrams. Their document-indexing system is
invented for explanation. Combine the component boundaries of the first with
the payload labels and transformations of the second when useful.
