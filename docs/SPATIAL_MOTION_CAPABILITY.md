# ATG Spatial Motion Capability

ATG may invoke AGENTROPOLIS `media.spatial.*` through capability-scoped requests only.

Allowed surface:
- request depth/pose/choreography/camera extraction
- request control composition or motion transfer
- receive normalized control packages, generated artifacts, health state, and receipts

Forbidden surface:
- provider source code
- provider filesystem paths
- raw API keys or credentials
- direct worker shell access
- unmetered bypass of Utility Grid routing

ATG signs the consumer/mission context and forwards the request to the Utility Grid. ASBE/54-T and budget policy determine whether execution is permitted and which approved adapter is selected.
