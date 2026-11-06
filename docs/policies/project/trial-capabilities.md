# Trial Capabilities And Platform Status

The desktop trial provides Sessions, Projects, Sessions Dashboard, explicitly
registered Local Context, keyword search, optional local embedding search,
Settings, onboarding and six offline Docs. Workstreams, Workflow, Auto Work,
Atlassian, Insights, Learning, Sources and Schema UI are not desktop capabilities.
Desktop composition excludes their optional hooks, routes and maintenance; legacy
organization records remain stored. The development web edition retains its
existing optional package selection. Context Search and Google Drive remain
suspended in both editions. The desktop authentication/route boundary still
applies independently of composition.

[Installation and storage](installation-and-storage.md) owns Mac paths and the
Git/agent local build entry. Originals stay at explicitly registered locations;
discovery never authorizes collection. Public model weights are shared Hub cache,
not app-owned cache. No model download is required for keyword search or Docs.

Windows native x86_64 is an expected future target, not a tested release. Proposed
paths are `%LOCALAPPDATA%\LocalBrain\Data` and
`%LOCALAPPDATA%\LocalBrain\Cache`; native Home and WSL Home/UNC paths are distinct.
[Expected paths and outstanding validation](../../plans/research/early-access-distribution-readiness.md#windows-expected-paths-and-storage--not-implemented-or-verified)
own concrete source/model discovery candidates and Windows-specific limitations.
A coding agent does not remove the need to port locking, process, packaging and
platform-specific document operations, then test an actual Windows installation,
optional AI setup, update and recovery. No existing Mac storage is moved.

Storage reports logical regular-file bytes, skips nested symlinks, deduplicates
hard links per location, and distinguishes a missing empty location from an
unreadable or partially measured location. Free space belongs to each actual
filesystem; locations sharing a volume share its free-space figure. Binary units
are labeled GiB. Shared model totals include other applications and models.
Backup eligibility remains the same installation, computer and schema; original
files and public weights are not included. Cache clearing never deletes originals
or the shared public model cache.
