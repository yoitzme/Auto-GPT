# Detailed review — November 13, 2026

Repository: yoitzme/Auto-GPT
Reviewed base commit: `3226ceaccf785c3d8e209d7a936d6dd8be0f78ed`

## Repair

Restrict credential-bearing clones to HTTPS github.com and suppress raw Git exceptions; pass Python filenames as argv; enforce the disabled-local-shell policy in the background command; return shell output without changing global cwd; preserve and atomically persist local memory, including clear/restart and provider/disk failure handling.

## Application review scope

CLI/agent loop -> command registry -> file and execution commands; workspace path resolver and restriction configuration; plugin loading and allow/deny policy; local embedding memory; SQLite scaffold and web request validation; Git clone credentials and requirements. The SQLite store has interpolated query methods but no live caller was found in this tree. The application intentionally executes operator-approved tools and is not a sandbox for hostile generated programs.

## Actual verification

Python 3.12.14: 14 targeted tests PASS using actual production function bodies and the actual local-memory module. Original tests reproduced truncation, unpaired memory after provider failure, forgotten data returning after restart, missing shell output/cwd leakage, unsafe Python filename interpolation, credential destination and error disclosure. GitPython 3.2.1 local init/commit/clone/read smoke PASS. `python -m compileall -q autogpt` PASS.

Commands (failures/limitations are preserved above and below):

- `python -m pytest -q tests/unit/test_audit_regressions.py tests/unit/test_execution_security.py tests/unit/test_local_memory_persistence.py tests/unit/test_git_credentials.py`
- `python -m compileall -q autogpt`
- `GitPython 3.2.1: temporary local Repo.init -> index.commit -> Repo.clone_from -> file read`
- `python -m pytest -q`

## Remaining blockers and unverified scope

Full pytest exited 2 with 12 collection errors: missing openai, requests, colorama and other legacy runtime dependencies. No full legacy dependency resolution, real LLM/provider calls, Docker daemon execution or Windows Python matrix was verified. Keep draft; no merge. The unpinned legacy requirements are not an audited resolved dependency graph. Both Dockerfile and .devcontainer/Dockerfile still select Python 3.10, which reached EOL on October 1, 2026 (https://devguide.python.org/versions/). A supported-Python container migration needs legacy dependency/build validation and remains open. No exhaustive assurance.

## Actions and reporting

The PR label workflow 55061438 was disabled and read back disabled_manually. Other push/PR YAML files were present but unregistered, so repository-level Actions permissions were disabled through the authenticated supported API and read back enabled=false before publication. No dispatch/rerun/status pass/deployment.
No authorized check/status reporting integration is configured. These are local test results tied to file hashes, not claimed green GitHub checks. Branch protections are not bypassed.

## Dependency scope

GitPython 3.1.31 was replaced by current 3.2.1 and exercised with local init/commit/clone/read. This does not establish a clean resolved graph for the remaining legacy unpinned requirements. No production provider or credential-bearing remote clone was executed.

## Candidate binding

The unchanged tree is anchored to the reviewed base above. SHA-256 hashes below bind every changed source/config/test file used in these checks; this report excludes itself to avoid a circular hash. Revalidate if these files change.

| Path | SHA-256 |
| --- | --- |
| autogpt/commands/execute_code.py | `40fd8c0532fb146e4fb40c73338753088b18771069d4888ed2f6aeba8b0dd744` |
| autogpt/commands/git_operations.py | `eba2e5c368d919bce562e7cc49d231548f1af49aca0ae76c3543b5b05d012e15` |
| autogpt/memory/local.py | `90a2ba94874377845d8857473c4448297ddf67027678a66fb76a97619570b8af` |
| requirements.txt | `894c272b077066e72673f1f8c45a7aa3410b24fb3a48b35604ff0b5cdea5bf33` |
| tests/unit/test_execution_security.py | `28cf05bae6986f2aa9d39e6ba28e1084693d319c2bc5617a151bf1420d387da7` |
| tests/unit/test_local_memory_persistence.py | `77f760b788a6ff72c50586bb573acea50c23fcb5c18c1dbb544f9c830f888cb7` |
| tests/unit/test_git_credentials.py | `ee825c86d4bde14ae647f2eb464098f1a4b12e23beb8292847e42f778f5dead1` |

## Rollback

Use a normal reviewed revert PR for the resulting repair commit, keeping Actions disabled. A source revert does not undo any deployment; none was performed.
