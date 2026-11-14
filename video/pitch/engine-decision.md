# Video Engine Decision — 60-Second Founder Pitch (`video/pitch/engine-decision.md`)

## Decision: HyperFrames + HTML/SVG Motion (`docs/workflow.svg`)

### Why HyperFrames:
1. **Accurate Web Architecture & UI Rendering**: TrialSwarm's core differentiator is its real-world clinical interface (`/`, `/judge`) and vector architecture (`docs/workflow.svg`). HyperFrames renders native DOM, SVG, and CSS animations with sub-pixel fidelity.
2. **Sub-second Re-renders**: Local headless Chrome composition without heavy 3D or After Effects toolchains.
3. **Deterministic Timelines**: Video beats are anchored directly to ElevenLabs character timestamps from `durations.json`.
4. **Offline Reproducibility**: Builds from repository assets with zero external proprietary binary dependencies.
