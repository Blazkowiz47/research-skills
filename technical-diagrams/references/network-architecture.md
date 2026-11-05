# Network architecture

Use for neural-network structure and computation inside a layer or mechanism.

## Visual vocabulary

- Feature tensors: translucent stacked sheets or volumes. Label axes/shapes when
  known; state which dimension the stack represents. Do not imply scale accuracy.
- Kernels or expert versions: separate gridded cuboids. Distinguish parameters
  from activations, and show selected/inactive versions with outlines and labels.
- Operators: compact symbols or labeled nodes for convolution, sums,
  concatenation, attention, normalization, and activation.
- Routers: distinct small components. Solid data arrows enter the router;
  dashed control/weight arrows leave it. A tensor sent to a router remains data.

## Operator notation

Use circled `+` for additive merge nodes throughout a figure family, including
weighted sums and bias/shared-branch additions. Do not alternate `+` and `Σ`
for the same merge. Use `×` for elementwise multiplication or scalar gating,
with shapes or labels making the distinction clear; use `@` for matrix
multiplication in explanatory formulas. Explicit publication notation can
override these defaults, but keep the chosen convention consistent.

Center glyphs visually inside operator nodes. Check the rendered glyph, not
just its text anchor. Keep convolution explicitly labeled; do not let a generic
multiplication symbol ambiguously stand for convolution.

Combine adjacent additive merges when mathematically valid and clearer, including
bias or shared-output inputs. Preserve gating, nonlinearities, shapes, and where
bias is applied; do not move an addition across a transformation or add bias twice.
Retain separate nodes if the intermediate result or execution order matters.

During inspection, trace tensor flow both into and within routers using solid
arrows, and decisions/gates using dashed arrows. Apply the shared inactive-state
rules to every nested operator and connection, not only expert containers.

## Preserve computation

Trace shapes, branch points, residual connections, and operator order. Distinguish
per-token, per-image, per-channel, and shared operations. Label repetition counts
and whether parameters are shared. Use symbolic dimensions if values are unknown.

Kernel mixing before convolution and mixing expert outputs are different graphs.
Do not substitute one for the other without a justified equivalence. Mark
proposed routing, illustrative weights, and unimplemented blocks as such.

## Modes

**Explain:** introduce the building blocks, expand one channel/token/block, then
show how it repeats in the full model. A representative expert bank is clearer
than depicting all channels at once.

**Present:** retain the main computational path and novel mechanism; use an inset
for detail. Put routine definitions in the caption. Preserve dimensions,
selection scope, and operation ordering needed to understand the claim.

## Reference example

- [Accepted translucent MoE preview](../assets/examples/network-architecture.png)
- [Editable SVG](../assets/examples/network-architecture.svg)

This example depicts a proposed depthwise MoE with four versions and top-2
selection. Those are example settings. It retains the accepted translucent
appearance with the revised circled-add notation, solid tensor input to the
router, and neutral grey inactive branches.
