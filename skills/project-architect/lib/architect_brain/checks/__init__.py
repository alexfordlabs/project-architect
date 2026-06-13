"""Auditor check registry.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0

Each check is a module exposing ``CHECK_ID: str`` + ``NAME`` + ``SEVERITY`` +
``run(state_dir) -> CheckResult``. ``ALL_CHECKS`` is the ordered registry the
auditor iterates (numeric CHECK_ID order). Modules prefixed ``_`` (``_docscan``,
``_state``, ``_findlib``) are shared helpers, not checks.

The full 35-check suite: 01-27 ported from v7 (Waves 5b/5c), 28-34 new in v8
(Wave 5d), 35 (user_provenance) added in v8.0.1.
``tests/test_all_checks_registered.py`` auto-discovers every
``check_NN_*`` module and asserts it is present here, so a forgotten registration
fails the suite.
"""

from architect_brain.checks import (
    check_01_links,
    check_02_affected_docs,
    check_03_decisions_in_docs,
    check_04_shellcheck,
    check_05_json_valid,
    check_06_claude_md_hierarchy,
    check_07_attribution_footer,
    check_08_no_placeholders,
    check_09_no_todos,
    check_10_yaml_frontmatter,
    check_11_schema_version,
    check_12_iso8601_timestamps,
    check_13_state_drift,
    check_14_adr_coverage,
    check_15_numerical_consistency,
    check_16_phase_gates,
    check_17_adr_files_exist,
    check_18_ledger_complete,
    check_19_audit_freshness,
    check_20_no_oob_phase_advance,
    check_21_settings_permissions_valid,
    check_22_cross_link_integrity,
    check_23_dependency_freshness,
    check_24_identity_hygiene,
    check_25_anonymity_threat_preflight,
    check_26_scaffold_executed,
    check_27_required_docs_generated,
    check_28_markdownlint,
    check_29_state_schema_valid,
    check_30_decisions_index_fresh,
    check_31_resume_test,
    check_32_catalog_topo_acyclic,
    check_33_vale_optional,
    check_34_build_pass,
    check_35_user_provenance,
    check_36_version_pins_recorded,
)

ALL_CHECKS = [
    check_01_links,
    check_02_affected_docs,
    check_03_decisions_in_docs,
    check_04_shellcheck,
    check_05_json_valid,
    check_06_claude_md_hierarchy,
    check_07_attribution_footer,
    check_08_no_placeholders,
    check_09_no_todos,
    check_10_yaml_frontmatter,
    check_11_schema_version,
    check_12_iso8601_timestamps,
    check_13_state_drift,
    check_14_adr_coverage,
    check_15_numerical_consistency,
    check_16_phase_gates,
    check_17_adr_files_exist,
    check_18_ledger_complete,
    check_19_audit_freshness,
    check_20_no_oob_phase_advance,
    check_21_settings_permissions_valid,
    check_22_cross_link_integrity,
    check_23_dependency_freshness,
    check_24_identity_hygiene,
    check_25_anonymity_threat_preflight,
    check_26_scaffold_executed,
    check_27_required_docs_generated,
    check_28_markdownlint,
    check_29_state_schema_valid,
    check_30_decisions_index_fresh,
    check_31_resume_test,
    check_32_catalog_topo_acyclic,
    check_33_vale_optional,
    check_34_build_pass,
    check_35_user_provenance,
    check_36_version_pins_recorded,
]
