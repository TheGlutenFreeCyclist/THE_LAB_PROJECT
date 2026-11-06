INC132 R153 — three-goal fixture audit (TEST only)

Read-only private JSON validator for POWER_1, SPRINTER, ENDURANCE_BASE. It does not change the runtime, issue workouts, mutate owner state, classify 30/15 as continuous POWER_1, or infer durability from Z2 duration. Verified work means unique matched activity record, resolved native source, precise date and ledger repeated-work equality. Tempo observations must have 600–1200 s bouts, comparable recovery, 80–88% of the event FTP and two independent dates to count as repeated protocol. Even a positive research observation is not an approved canonical Tempo template.

Private execution (NEVER commit a fixture or its unredacted output): python qa/nova_test_lab/inc132_r153/goal_fixture_audit.py /private/athlete.json --out /private/sanitized.json

Synthetic safety suite: python -m unittest discover -s qa/nova_test_lab/inc132_r153/tests -p test_goal_fixture_audit.py -v

All three goals stay RESEARCH_ONLY_NOT_ISSUABLE until separate scientific sign-off, issuer proof, owner-bound real replay, and clearance. No production deploy.
