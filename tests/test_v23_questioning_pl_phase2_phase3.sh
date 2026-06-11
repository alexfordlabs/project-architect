#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: Apache-2.0
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# PL question batches in questioning-flow.md (v8 phase placement).
# Verifies the reference documents two PL sub-sections, triggered when the
# project.sub_type decision is one of the 6 PL variants:
#   - Tech Stack phase (Phase 4): pl.impl_strategy (5 values) + pl.host_runtime (14 values)
#   - Architecture phase (Phase 3): pl.paradigm (6 values) + pl.type_system (6 values)
# Each batch must cross-reference its target template(s).

source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/questioning-flow.md"

assert_file_exists "$REF" 'questioning-flow.md must exist'

CONTENT=$(cat "$REF")

# The PL impl_strategy/host_runtime batch is placed in the Tech Stack phase (Phase 4).
assert_contains "$CONTENT" 'Tech Stack (Phase 4)' 'PL impl_strategy batch must be placed in the Tech Stack phase (Phase 4)'

# --- Phase 2 PL section presence ---
# A dedicated Phase 2 PL sub-section must exist with PL-specific batch wording.
assert_contains "$CONTENT" 'Phase 2' 'questioning-flow.md must reference Phase 2'
assert_contains "$CONTENT" 'PL-specific' 'questioning-flow.md must label the Phase 2 PL batch as PL-specific'

# Trigger condition: sub_type in PL set.
assert_contains "$CONTENT" 'project.sub_type' 'Phase 2 PL batch must trigger on state.decisions.project.sub_type'

# --- impl_strategy (5 values) ---
assert_contains "$CONTENT" 'impl_strategy' 'Phase 2 PL batch must introduce impl_strategy axis'
assert_contains "$CONTENT" 'tree_walking_interpreter' 'impl_strategy must include tree_walking_interpreter'
assert_contains "$CONTENT" 'bytecode_vm' 'impl_strategy must include bytecode_vm'
assert_contains "$CONTENT" 'native_compiler' 'impl_strategy must include native_compiler'
assert_contains "$CONTENT" 'transpiler' 'impl_strategy must include transpiler'
assert_contains "$CONTENT" 'hosted_embedded' 'impl_strategy must include hosted_embedded'

# --- host_runtime (14 values; require at least 7 of 14 named verbatim) ---
assert_contains "$CONTENT" 'host_runtime' 'Phase 2 PL batch must introduce host_runtime axis'
HR_HITS=0
for v in llvm mlir cranelift qbe truffle jvm beam wasm wasm_component js_host python_embedded rust_host native_no_runtime custom_vm; do
  if [[ "$CONTENT" == *"$v"* ]]; then
    HR_HITS=$((HR_HITS + 1))
  fi
done
if (( HR_HITS >= 7 )); then
  PASS_COUNT=$((PASS_COUNT + 1))
else
  FAIL_COUNT=$((FAIL_COUNT + 1))
  FAIL_MESSAGES+=("FAIL: host_runtime must mention at least 7 of 14 enum values; found only $HR_HITS")
fi

# Cross-reference: Phase 2 PL batch must point at tech-stack-options.md (Task 12).
assert_contains "$CONTENT" 'tech-stack-options.md' 'Phase 2 PL batch must cross-reference tech-stack-options.md'

# --- Phase 3 PL section presence ---
assert_contains "$CONTENT" 'Phase 3' 'questioning-flow.md must reference Phase 3'

# --- paradigm (6 values) ---
assert_contains "$CONTENT" 'paradigm' 'Phase 3 PL batch must introduce paradigm axis'
for v in imperative functional logic oop multi_paradigm data_oriented; do
  assert_contains "$CONTENT" "$v" "paradigm enum must include: $v"
done

# --- type_system (6 values) ---
assert_contains "$CONTENT" 'type_system' 'Phase 3 PL batch must introduce type_system axis'
for v in static_strong static_gradual dynamic dependent affine_linear none_untyped; do
  assert_contains "$CONTENT" "$v" "type_system enum must include: $v"
done

# Cross-references to PL templates.
assert_contains "$CONTENT" 'TYPE_SYSTEM.md' 'Phase 3 PL batch must cross-reference TYPE_SYSTEM.md template'
assert_contains "$CONTENT" 'BOOTSTRAP_PLAN.md' 'Phase 2 PL batch must cross-reference BOOTSTRAP_PLAN.md template'
assert_contains "$CONTENT" 'SEMANTICS.md' 'PL batches must cross-reference SEMANTICS.md template'

# Flat decision keys documented (v8 — no monolith state.decisions).
assert_contains "$CONTENT" 'pl.impl_strategy' 'Tech Stack PL batch must persist the flat key pl.impl_strategy'
assert_contains "$CONTENT" 'pl.host_runtime' 'Tech Stack PL batch must persist the flat key pl.host_runtime'
assert_contains "$CONTENT" 'pl.paradigm' 'Architecture PL batch must persist the flat key pl.paradigm'
assert_contains "$CONTENT" 'pl.type_system' 'Architecture PL batch must persist the flat key pl.type_system'

test_summary
