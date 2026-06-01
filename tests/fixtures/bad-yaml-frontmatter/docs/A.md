---
title: Bad
nested:
  key1: value1
 key2: value2
---

# Body

This file has a malformed YAML frontmatter block above. The
`key2` line is indented by ONE space while `key1` is indented by
TWO — PyYAML cannot resolve this into a valid mapping and raises
a YAMLError. The check_10 auditor must flag this file.
