# A (contains a TODO marker)

This fixture file deliberately contains a TODO marker so
check_09_no_todos can flag it as a WARNING finding. The marker on the
next line is what the check matches.

TODO: do thing — wire up the missing handoff step before Phase 5.

A real authored doc would either resolve the TODO inline, move it to
BACKLOG.md (which is excluded from this check by design), or accept it
as a documented known gap.
