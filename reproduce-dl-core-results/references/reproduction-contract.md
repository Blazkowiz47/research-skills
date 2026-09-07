# Reproduction contract

Before expensive execution, write one small JSON record in the experiment repository.
Link evidence for each material choice; leave unresolved values explicit. Reuse an
existing experiment manifest if it already represents these fields.

- Target paper/version and exact table row, metric value, units, and direction.
- Official implementation commit or tag, plus file/function references.
- Local commit and uncommitted-change reference; dependency lock hash, Python,
  Torch, accelerator/runtime versions, and hardware allocation.
- Dataset manifests or checksums, splits, record counts, preprocessing, and protocol.
- Realized configuration path and hash, total optimizer steps, checkpoint selection,
  evaluation command, folds, thresholds, and aggregation.
- Comparison rule established before inspecting outcomes: acceptable absolute gap,
  tolerance rationale, seed list, and whether repeated runs or uncertainty estimates
  are needed. Never choose a tolerance retrospectively to claim a match.
- Compute/time budget, existing active run, resume checkpoint, and stop conditions.

Use meaningful field names such as `target`, `sources`, `environment`, `data`,
`configuration`, `evaluation`, and `comparison`. Attach actual realized values after
validation. A filled manifest is not evidence that its values were verified.

Distinguish a faithful protocol with an unexplained metric gap from a protocol
mismatch. If the official code contradicts the paper, retain both accounts and
record the chosen protocol. Do not silently treat the latest repository as the
code used for the published result. Match the source version to the target result.

Report per-seed results and the aggregate required by the protocol. Keep validation
selection separate from final test evaluation. Never tune repeatedly on the test
set to close the published gap.
