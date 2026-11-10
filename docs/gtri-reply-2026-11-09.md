Subject: Re: Bug Report sysmlpy 0.105.0 semantic-validation gaps found with OpenSysML/SysON

Jon,

Both gaps are fixed in sysmlpy 0.106.0 (tagged, on PyPI), with your four repro files pinned as permanent regression tests.

1. Allocation endpoints

analyze() now resolves allocation endpoints and reports an
ALLOCATION_ENDPOINT_UNRESOLVED error for every form — binary
(allocate a to b), n-ary (allocate (a, b, c); every end checked), chained
(allocate a.p to b.q), qualified (Architecture::Source), and star-imported.
The public API gap is fixed too: allocation.source_elements /
target_elements now resolve qualified and feature-chain names, so your
QualifiedAllocation repro returns the Source and Target elements instead of
empty lists.

The TypedAllocation file exposed a third bug you didn't report — the
'end :>> source : Architecture::Source;' members of an allocation
definition were grammar-only, so their typings were never checked and the
nested 'allocate source to target;' couldn't resolve.  Definition ends now
report an ALLOCATION_END_TYPE_UNRESOLVED error when their type doesn't
resolve, and the nested allocate resolves through the end's declared type.

One deliberate divergence, documented rather than "fixed": sysmlpy resolves
'allocate Architecture::Source to Target;' from inside Functions — the same
resolver handles typings, where the identical spelling is silent ('part s :
Architecture::Source;' has always been clean).  OpenSysML disagrees: I ran
your four files through bin/sysml -validate from origin/develop
(0.12.1-998-gddc4a547fe).  It rejects the qualified form with
error[connector-end-referent]: "Must be a valid feature" on BOTH ends — and
it also rejects the star-imported QualifiedAllocationImported form, the one
your report describes as making it accept the test.  So on current develop
that workaround doesn't hold.  Both verdicts are pinned in
tests/gtri_portability_test.py so the delta stays mechanical, and the
write-up is in docs/COMPARISON.md.

2. One-sided interfaces

Concrete interface definitions now must carry at least two related
elements; a zero- or one-end definition is an error with OpenSysML's
message verbatim ("Must have at least two related elements", KerML 1.1
§8.3.3.5/§8.3.4.7) so cross-tool runs diff cleanly.  Abstract and variation
declarations are exempt, and ends inherited through :> count toward the
two.  Your SingleItemInterface repro and the CCMM EthernetInterface shape
are both flagged.  Note: a one-end 'connect X;' and a one-feature 'bind
X;' can't be written at all in the grammar — those two are caught upstream
of semantics, noted in the test module.

Where the tools stand after 0.106.0: both tools now agree on all four of
your repro files — sysmlpy accepts QualifiedAllocation (+TypedAllocation,
+imported form), rejects SingleItemInterface; OpenSysML accepts only
TypedAllocation.

Tests: tests/issue43_test.py (15), tests/issue44_test.py (14),
tests/gtri_portability_test.py (12; 4 skip without a built OpenSysML).
Issues: mycr0ft/sysmlpy#43, #44, both closed with the fix commits.

Regards,
Jon
