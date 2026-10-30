# Week 10 Break It Report — TEMPLATE (no verified breaks yet)

**Attack team:** Group 11 (Huseyin Simsek and Gustavo Pepe)  
**Assigned defender / anonymized code ID:** [await assignment]  
**Authorized target / commit SHA:** [await exchange]  
**Provided official test harness and oracle:** [await course files]  
**Date and environment:** [fill in]

## Test case [number] — [only after a confirmed break]

- **Issue and category:** [authorization / state validation / XSS / SQLi / session / other]
- **Security or correctness impact:** [clear observable violation]
- **Preconditions:** [roles, seeded state, credentials provided by assignment]
- **Exact target version:** [commit SHA or provided release hash]
- **Payload / request sequence:** [minimum reproducible commands or script invocation]
- **Expected behavior under defender's spec:** [state expected response / invariant]
- **Observed behavior:** [actual response, DB state, reproducible evidence]
- **Executable regression test file:** [path to real case, not a hypothetical]
- **Repeat count and confidence:** [e.g., 3/3]
- **Why this is exploitable:** [root cause and authorization/state boundary]
- **Security weighting:** [apply course-specified scoring only after classification]

## Candidate experiments (not findings)

1. As Guest, direct-request the staff event endpoint and admin role-change endpoints; verify 403 and no DB writes.
2. Supply a different person's ID on the history page; verify the guest cannot see or infer that person's records.
3. Submit duplicate entry, leave-room-before-enter, and wrong-room-leave events; verify 409 and unchanged event count.
4. Submit two entry requests concurrently for the same person; verify only one is accepted.
5. Test SQL metacharacters in validated identifiers and harmless `<script>` text in editable display fields; verify no SQL access or executable response output.
6. Submit a write without a CSRF token; verify it is rejected.
7. Test repeated incorrect logins, session expiry, page-size bounds and request-size limits.

**Important:** These are planned tests only. They do *not* establish the presence of a vulnerability. Do not claim or submit a break without a real, reproducible, authorized failing test against the assigned peer's code.
