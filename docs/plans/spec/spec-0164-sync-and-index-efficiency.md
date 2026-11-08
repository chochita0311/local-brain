# SPEC-0164: Sync And Index Efficiency

- Status: `approved`
- Feature: [FEAT-0164](../feature/feat-0164-sync-and-index-efficiency.md)

Prune hidden/ignored Local Context descendant directories before traversal while
preserving the accepted sorted path set, symlink behavior, cancellation, failure
and stale-document rules. Read source-file metadata once per coherent processing
stage instead of once per path; retain fresh filesystem observations and account
for earlier lifecycle writes before snapshotting. Reduce repeated workspace
attribution lookups within one Usage-store call while retaining per-record
observation times, source ownership and all existing frozen snapshot rules.

Search preparation keeps resumable staging vectors. Replace per-fragment current
vector existence queries with generation-local membership and batch prior-vector
lookups in bounded groups, preserving fragment order, reuse/encode counts, vector
validation, cancellation, force/restart behavior, fingerprints, evidence IDs and
atomic reader publication. Shared compatibility backfills must preserve required
NULL repair while avoiding updates to already-filled rows. No schema admission,
source parsing, price, result ranking or native distribution changes.
