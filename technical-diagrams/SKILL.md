---
name: technical-diagrams
description: Create or revise technical diagrams for neural networks, software systems, data pipelines, method-call sequences, and control flow. Use when asked to draw an architecture, explain data flow, show call order, or visually explain how a system works, even without naming this skill. Also use for system explanations when a diagram materially improves understanding. Respect requests for text only; excludes statistical plots and decorative illustrations.
---

# Technical Diagrams

Explain structure and behavior using Sushrut's translucent pastel visual style.
Keep the diagram proportional to the question; a single useful view is enough.

## Select the view

Read [visual-style.md](references/visual-style.md) and only the relevant type
reference below. Open its example only when useful for visual calibration.
Do not preload every reference or example.

| Question | Read |
|---|---|
| Layers, tensors, branches, or model mechanisms | [network-architecture.md](references/network-architecture.md) |
| Components, boundaries, pipelines, or data transformations | [system-and-data-flow.md](references/system-and-data-flow.md) |
| Which object calls which method, and in what order | [sequence.md](references/sequence.md) |
| Conditions, branching, loops, failures, or retries | [control-flow.md](references/control-flow.md) |

Combine views only when they answer distinct parts of the request. A system
overview followed by one method sequence is often enough; do not produce a
diagram gallery by default.

## Select the mode

- **Explain** is the default: introduce unfamiliar visual elements, expand one
  representative unit, and connect it to the whole. Use short explanatory labels.
- **Present** applies to papers, slides, publication, or an explicit request:
  make the composition compact and readable at its intended display size.
  Papers need legible notation at column width; slides need larger labels and
  fewer details. Preserve technical meaning when reducing density.

Infer the type and mode from the request. Ask only when an unresolved choice
would materially change the result. Explicit user style and format choices
override these defaults.

## Ground, draw, inspect

1. Establish the question and scope. For an existing system, inspect the relevant
   instructions, code, configs, and docs without inventorying the whole project.
   Trace actual calls or transformations; distinguish implementation, proposals,
   and illustrative examples. Keep source pointers in accompanying prose when
   they would clutter the figure. Mark unresolved connections rather than inventing them.
2. Choose the smallest view that preserves the important objects, boundaries,
   ordering, and data. Apply the selected reference and shared style.
3. Produce an editable vector artifact and a rendered preview when supported.
   Use the user's requested format/tool first; otherwise follow the rendering
   guidance in the style reference. Save to the requested destination or the
   project's established diagram/artifact location; use a separate local output
   directory if none exists. Do not change implementation to produce a diagram.
4. Inspect the rendered result at its intended size. Check arrow endpoints,
   labels, clipping, overlaps, contrast, and technical correctness. Fix problems
   before presenting it. If rendering is unavailable, say what remains unchecked.
5. Show the diagram inline where supported and link its editable source. Briefly
   explain its scope or assumptions. Revise the relevant view when feedback arrives.

Diagram requests authorize diagram artifacts, not training, production jobs,
dataset changes, external publication, or unrelated project edits.
