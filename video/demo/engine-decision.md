# Video Engine Decision — 3-Minute Deep Dive Product Demo (`video/demo/engine-decision.md`)

## Decision: HyperFrames + Web Workstation Capture (`src/web/static/`)

### Architecture Rationale:
1. **Screen-Accurate Clinical Demonstration**: The demo features real web UI screens (`/`, `/judge`), reactive DOM events, ARIA tabs, line-citation pill clicks, and native `<dialog>` modals.
2. **Deterministic Beat Synchronization**: Narrated scenes synchronize with microsecond precision against `video/demo/assets/audio/vo/durations.json` produced by ElevenLabs.
3. **No Phantom Render Farms**: Renders on-device using headless Chromium and ffmpeg with zero external cloud video credits.
