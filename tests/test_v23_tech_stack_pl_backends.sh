#!/usr/bin/env bash
# Author: Alexander Ford <alex@alexfordlabs.com>
# License: MIT
# Project: project-architect (https://github.com/alexfordlabs/project-architect)
#
# v2.3 Task 12: PL implementation backends in tech-stack-options.md.
# Verifies the new "Programming language implementation backends" section
# documents all 14 host_runtime enum values with 2026 status anchors and
# points back to the BOOTSTRAP_PLAN.md / TYPE_SYSTEM.md templates.

source "$(dirname "$0")/lib/test_helpers.sh"

REF="$REPO_ROOT/skills/project-architect/references/tech-stack-options.md"
assert_file_exists "$REF" "tech-stack-options.md reference must exist"

CONTENT=$(cat "$REF")

# Section header + version markers
assert_contains "$CONTENT" '## Programming language implementation backends' \
  'new PL backends section header must be present'
assert_contains "$CONTENT" 'v2.3' \
  'section must carry v2.3 marker'
assert_contains "$CONTENT" 'Sketch F' \
  'section must reference Sketch F'

# All 14 host_runtime enum values (matches state-schema.md)
assert_contains "$CONTENT" '`llvm`'              'host_runtime: llvm'
assert_contains "$CONTENT" '`mlir`'              'host_runtime: mlir'
assert_contains "$CONTENT" '`cranelift`'         'host_runtime: cranelift'
assert_contains "$CONTENT" '`qbe`'               'host_runtime: qbe'
assert_contains "$CONTENT" '`truffle`'           'host_runtime: truffle'
assert_contains "$CONTENT" '`jvm`'               'host_runtime: jvm'
assert_contains "$CONTENT" '`beam`'              'host_runtime: beam'
assert_contains "$CONTENT" '`wasm`'              'host_runtime: wasm'
assert_contains "$CONTENT" '`wasm_component`'    'host_runtime: wasm_component'
assert_contains "$CONTENT" '`js_host`'           'host_runtime: js_host'
assert_contains "$CONTENT" '`python_embedded`'   'host_runtime: python_embedded'
assert_contains "$CONTENT" '`rust_host`'         'host_runtime: rust_host'
assert_contains "$CONTENT" '`native_no_runtime`' 'host_runtime: native_no_runtime'
assert_contains "$CONTENT" '`custom_vm`'         'host_runtime: custom_vm'

# Key 2026 version anchors
assert_contains "$CONTENT" 'LLVM 22'        'must cite LLVM 22.x'
assert_contains "$CONTENT" 'Wasm 3.0'       'must cite Wasm 3.0 (Sept 2025 W3C)'
assert_contains "$CONTENT" 'Java 25 LTS'    'must cite Java 25 LTS'
assert_contains "$CONTENT" 'Mojo'           'must cite Mojo as MLIR proof'
assert_contains "$CONTENT" 'Python 3.14'    'must cite Python 3.14'
assert_contains "$CONTENT" 'GraalVM 24/25 LTS' 'must cite GraalVM 24/25 LTS for truffle'
assert_contains "$CONTENT" 'WASI 0.2'       'must cite WASI 0.2 stable for wasm_component'

# Cross-references to PL templates
assert_contains "$CONTENT" 'BOOTSTRAP_PLAN' 'must point to BOOTSTRAP_PLAN template'
assert_contains "$CONTENT" 'TYPE_SYSTEM'    'must point to TYPE_SYSTEM template'

# Footer attribution preserved at file end
assert_contains "$CONTENT" 'Skillfully made with' 'attribution footer required'

test_summary
