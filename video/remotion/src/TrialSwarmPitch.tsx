import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const FPS = 30;
const VO_GAP = 8; // ~0.27s clean breath between narration clips

// Strictly sequential scenes (NO overlapping <Sequence>s -> zero ghosting)
const D = {
  s1: 322, // 10.73s (audio 10.45s = 314f + 8f breath)
  s2: 333, // 11.10s (audio 10.82s = 325f + 8f breath)
  s3a: 245, // 8.17s LIGHT 5-agent workflow
  s3b: 258, // 8.60s DARK /swarm board + R1 conversion
  s4: 378, // 12.60s (audio 12.35s = 370f + 8f breath)
  s5a: 132, // 4.40s LIGHT scorecard
  s5b: 130, // 4.33s DARK end card (total 1798f = 59.93s <= 60s)
};

const F = {
  s1: 0,
  s2: D.s1,
  s3a: D.s1 + D.s2,
  s3b: D.s1 + D.s2 + D.s3a,
  s4: D.s1 + D.s2 + D.s3a + D.s3b,
  s5a: D.s1 + D.s2 + D.s3a + D.s3b + D.s4,
  s5b: D.s1 + D.s2 + D.s3a + D.s3b + D.s4 + D.s5a,
};

export const TOTAL_FRAMES = D.s1 + D.s2 + D.s3a + D.s3b + D.s4 + D.s5a + D.s5b; // 1798f = 59.93s

const DARK = {
  bg: '#0D1117',
  surface: '#191D22',
  line: '#2A3038',
  accent: '#E8A33D',
  red: '#EF4444',
  green: '#10B981',
  blue: '#3B82F6',
  text: '#F4F1EA',
  muted: '#AAB4C0',
};

const LIGHT = {
  bg: '#F7F5F2',
  card: '#FFFFFF',
  ink: '#1B1D21',
  muted: '#565C64',
  accent: '#C7622D',
  accentSoft: '#F7E7DC',
  line: '#D9D5CE',
  green: '#059669',
  red: '#DC2626',
};

const SANS =
  '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, "Segoe UI", sans-serif';
const MONO = 'ui-monospace, "SFMono-Regular", Menlo, Monaco, monospace';

// Sanad V2 style SceneIn: no overlapping cross-fades, crisp fade-up from dark for light scenes
const SceneIn: React.FC<{
  first?: boolean;
  fromDark?: boolean;
  theme?: 'dark' | 'light';
  children: React.ReactNode;
}> = ({ first, fromDark, theme = 'dark', children }) => {
  const frame = useCurrentFrame();
  const opacity = first
    ? 1
    : fromDark
    ? interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' })
    : interpolate(frame, [0, 6], [0.35, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        background: theme === 'light' ? LIGHT.bg : DARK.bg,
        color: theme === 'light' ? LIGHT.ink : DARK.text,
        fontFamily: SANS,
        opacity,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const TopBar: React.FC<{ tag: string; step: string; theme?: 'dark' | 'light' }> = ({
  tag,
  step,
  theme = 'dark',
}) => {
  const isLight = theme === 'light';
  return (
    <div
      style={{
        position: 'absolute',
        top: 36,
        left: 80,
        right: 80,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: '8px 18px',
          borderRadius: 999,
          border: `1.5px solid ${isLight ? LIGHT.accent : DARK.accent}`,
          background: isLight ? LIGHT.accentSoft : 'rgba(232,163,61,0.12)',
          color: isLight ? LIGHT.accent : DARK.accent,
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 1.0,
          whiteSpace: 'nowrap',
        }}
      >
        {tag}
      </div>
      <div style={{ fontFamily: MONO, fontSize: 22, color: isLight ? LIGHT.muted : DARK.muted, whiteSpace: 'nowrap' }}>
        {step}
      </div>
    </div>
  );
};

/* ── SCENE 1 (0–10.7s): Buyer Stake + 120-Cohort Failure Grid (stays red/amber until VO finishes) */
const Scene1Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const h1 = spring({ frame, fps, config: { damping: 20, stiffness: 120 } });
  const litCells = Math.round(
    interpolate(frame, [8, 220], [0, 120], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })
  );
  // Reveal TrialSwarm solution badge only in the final 2 seconds after "IRB protocol deviation"
  const solutionAt = 240;
  const solIn = spring({ frame: Math.max(0, frame - solutionAt), fps, config: { damping: 20 } });

  return (
    <SceneIn first>
      <TopBar tag="ONCOLOGY CRC PRE-SCREENING · REAL STAKE" step="01 / 07" />

      <div style={{ position: 'absolute', left: 80, top: 140, width: 910 }}>
        <div
          style={{
            fontSize: 90,
            fontWeight: 800,
            lineHeight: 1.03,
            letterSpacing: -2.5,
            transform: `translateY(${(1 - h1) * 24}px)`,
            opacity: h1,
          }}
        >
          <span style={{ color: DARK.accent }}>4 Hours</span> Lost.
          <br />
          <span style={{ color: DARK.red }}>1 Missed Trap.</span>
        </div>

        <div style={{ marginTop: 26, fontSize: 32, color: DARK.muted, lineHeight: 1.38 }}>
          One missed steroid conversion = <b style={{ color: DARK.red }}>IRB protocol deviation</b>.
        </div>

        <div style={{ marginTop: 38, display: 'flex', gap: 24 }}>
          <div
            style={{
              background: DARK.surface,
              border: `2px solid ${DARK.red}`,
              borderRadius: 18,
              padding: '22px 28px',
              minWidth: 290,
            }}
          >
            <div style={{ fontSize: 20, color: DARK.red, fontWeight: 700, whiteSpace: 'nowrap' }}>
              NAIVE LLM BASELINE
            </div>
            <div style={{ fontSize: 56, fontWeight: 800, marginTop: 6 }}>47.5%</div>
            <div style={{ fontSize: 22, color: DARK.muted }}>63 / 120 cases misclassified</div>
          </div>

          <div
            style={{
              background: DARK.surface,
              border: `2px solid ${frame >= solutionAt ? DARK.green : DARK.line}`,
              borderRadius: 18,
              padding: '22px 28px',
              minWidth: 290,
              opacity: frame >= solutionAt ? 0.35 + 0.65 * solIn : 0.4,
            }}
          >
            <div style={{ fontSize: 20, color: DARK.green, fontWeight: 700, whiteSpace: 'nowrap' }}>
              TRIALSWARM /SWARM
            </div>
            <div style={{ fontSize: 56, fontWeight: 800, marginTop: 6, color: DARK.green }}>100.0%</div>
            <div style={{ fontSize: 22, color: DARK.muted }}>120 / 120 · Rules R1–R6</div>
          </div>
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          right: 80,
          top: 150,
          width: 740,
          background: DARK.surface,
          border: `2px solid ${DARK.line}`,
          borderRadius: 22,
          padding: 30,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <span style={{ fontFamily: MONO, fontSize: 19, fontWeight: 700, whiteSpace: 'nowrap' }}>
            BENCHMARK COHORT (n = 120)
          </span>
          <span style={{ fontFamily: MONO, fontSize: 18, color: DARK.red, whiteSpace: 'nowrap' }}>
            RED = NAIVE LLM MISSES (63)
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 10 }}>
          {Array.from({ length: 120 }, (_, i) => {
            const isMiss = i >= 57;
            const active = i < litCells;
            const bg = !active ? '#232934' : isMiss ? DARK.red : DARK.accent;
            return (
              <div
                key={i}
                style={{
                  height: 36,
                  borderRadius: 8,
                  background: bg,
                  opacity: active ? 0.95 : 0.35,
                }}
              />
            );
          })}
        </div>
        <div style={{ marginTop: 18, fontSize: 20, color: DARK.muted, fontFamily: MONO, whiteSpace: 'nowrap' }}>
          ClinicalTrials.gov v2: NCT04613596 · NCT04787042 · NCT06890598
        </div>
      </div>
    </SceneIn>
  );
};

/* ── SCENE 2 (10.7–21.8s): PT-102 Trap -> Rule R1 Reveal AFTER "falsely clear him" ─────────── */
const Scene2Trap: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const leftIn = spring({ frame, fps, config: { damping: 20 } });
  const rightIn = spring({ frame: Math.max(0, frame - 45), fps, config: { damping: 20 } });
  // Trigger Rule R1 reveal only at frame 245 (after VO says "and falsely clear him")
  const revealAt = 245;
  const slam = spring({ frame: Math.max(0, frame - revealAt), fps, config: { damping: 20, stiffness: 120 } });

  return (
    <SceneIn>
      <TopBar tag="CLINICAL TRAP · CASE PT-102 (MARCUS VANCE)" step="02 / 07" />

      <div style={{ position: 'absolute', left: 80, top: 122, fontSize: 56, fontWeight: 800, letterSpacing: -1.5 }}>
        {frame >= revealAt ? 'Rule R1 Catches What LLMs Miss' : 'The Glucocorticoid Potency Trap'}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 80,
          top: 215,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 36,
        }}
      >
        <div
          style={{
            background: DARK.surface,
            border: `2px solid ${DARK.line}`,
            borderRadius: 20,
            padding: 34,
            opacity: leftIn,
            transform: `translateY(${(1 - leftIn) * 20}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 22, color: DARK.accent }}>EHR LINE 26 · MEDICATIONS</div>
          <div style={{ fontSize: 42, fontWeight: 800, marginTop: 16 }}>Dexamethasone 2 mg BID</div>
          <div style={{ fontSize: 32, color: DARK.muted, marginTop: 12 }}>
            Raw daily dose = <b style={{ color: DARK.text }}>4.0 mg/day</b>
          </div>
          <div
            style={{
              marginTop: 22,
              padding: 18,
              borderRadius: 12,
              background: DARK.bg,
              fontFamily: MONO,
              fontSize: 22,
              color: DARK.muted,
              borderLeft: `5px solid ${DARK.blue}`,
            }}
          >
            Protocol NCT04613596 (Line 20):
            <br />
            <span style={{ color: DARK.text }}>Excludes systemic steroids &gt; 10 mg/day Prednisone eq.</span>
          </div>
        </div>

        <div
          style={{
            background: DARK.surface,
            border: `2.5px solid ${DARK.red}`,
            borderRadius: 20,
            padding: 34,
            opacity: rightIn,
            transform: `translateY(${(1 - rightIn) * 20}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 22, color: DARK.red }}>NAIVE SINGLE-PROMPT LLM</div>
          <div
            style={{
              display: 'inline-block',
              marginTop: 16,
              padding: '10px 24px',
              borderRadius: 12,
              background: 'rgba(239,68,68,0.18)',
              border: `2px solid ${DARK.red}`,
              color: DARK.red,
              fontSize: 40,
              fontWeight: 800,
            }}
          >
            ELIGIBLE (FALSE PASS)
          </div>
          <div style={{ fontSize: 30, color: DARK.muted, marginTop: 20, lineHeight: 1.38 }}>
            Compares <b style={{ color: DARK.text }}>4 mg &lt;= 10 mg</b> without steroid potency equivalence.
          </div>
        </div>
      </div>

      {frame >= revealAt && (
        <div
          style={{
            position: 'absolute',
            left: 80,
            right: 80,
            bottom: 135,
            background: 'linear-gradient(90deg, rgba(232,163,61,0.2), rgba(25,29,34,0.96))',
            border: `2.5px solid ${DARK.accent}`,
            borderRadius: 20,
            padding: '22px 34px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            opacity: slam,
            transform: `translateY(${(1 - slam) * 24}px)`,
          }}
        >
          <div>
            <div style={{ fontFamily: MONO, fontSize: 22, color: DARK.accent, fontWeight: 700 }}>
              RULE R1 DETERMINISTIC CONVERSION
            </div>
            <div style={{ fontFamily: MONO, fontSize: 36, fontWeight: 800, marginTop: 6 }}>
              4.0 mg × (5.0 / 0.75) = <span style={{ color: DARK.accent }}>26.67 mg/day</span> Prednisone eq
            </div>
          </div>
          <div
            style={{
              padding: '14px 28px',
              borderRadius: 12,
              background: DARK.red,
              color: '#fff',
              fontSize: 30,
              fontWeight: 800,
            }}
          >
            CONTRAINDICATED
          </div>
        </div>
      )}
    </SceneIn>
  );
};

/* ── SCENE 3A (LIGHT Editorial, 5 Agents Explicit) ──────────────────────────────────────────── */
const Scene3aWorkflowLight: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const c1 = spring({ frame: Math.max(0, frame - 8), fps, config: { damping: 20 } });
  const c2 = spring({ frame: Math.max(0, frame - 65), fps, config: { damping: 20 } });
  const c3 = spring({ frame: Math.max(0, frame - 135), fps, config: { damping: 20 } });
  const c4 = spring({ frame: Math.max(0, frame - 185), fps, config: { damping: 20 } });

  return (
    <SceneIn fromDark theme="light">
      <TopBar tag="ANTIGRAVITY /SWARM · 5-AGENT ARCHITECTURE" step="03 / 07" theme="light" />

      <div style={{ position: 'absolute', left: 80, top: 112 }}>
        <div style={{ fontSize: 62, fontWeight: 800, letterSpacing: -1.5 }}>
          Five Agents. One Deterministic Gate.
        </div>
        <div style={{ fontSize: 29, color: LIGHT.muted, marginTop: 6 }}>
          Parallel Gemini 2.5 extraction → physician-signed Rules R1–R6
        </div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 80,
          top: 265,
          display: 'grid',
          gridTemplateColumns: '1fr 48px 1.25fr 48px 1fr 48px 1fr',
          alignItems: 'center',
        }}
      >
        {/* 1: @coordinator */}
        <div
          style={{
            background: LIGHT.card,
            border: `2px solid ${LIGHT.line}`,
            borderRadius: 22,
            padding: '28px 24px',
            minHeight: 370,
            opacity: c1,
            transform: `translateY(${(1 - c1) * 20}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 21, fontWeight: 700, color: LIGHT.accent }}>1 · @coordinator</div>
          <div style={{ fontSize: 42, fontWeight: 800, marginTop: 10 }}>Dispatch</div>
          <div style={{ fontSize: 26, color: LIGHT.muted, lineHeight: 1.32, marginTop: 14 }}>
            Stages swarm run and SHA-256 CRC sign-off packet.
          </div>
        </div>

        <div style={{ textAlign: 'center', fontSize: 38, color: LIGHT.accent, opacity: c2 }}>→</div>

        {/* 2 & 3: Parallel @extractor + @phenotyper */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18, opacity: c2, transform: `translateY(${(1 - c2) * 20}px)` }}>
          <div style={{ background: LIGHT.card, border: `2px solid ${LIGHT.accent}`, borderRadius: 20, padding: '22px 24px' }}>
            <div style={{ fontFamily: MONO, fontSize: 20, fontWeight: 700, color: LIGHT.accent }}>
              2 · @extractor (Gemini Flash)
            </div>
            <div style={{ fontSize: 25, color: LIGHT.ink, fontWeight: 600, marginTop: 6 }}>
              Parses protocol lines (NCT v2)
            </div>
          </div>
          <div style={{ background: LIGHT.card, border: `2px solid ${LIGHT.accent}`, borderRadius: 20, padding: '22px 24px' }}>
            <div style={{ fontFamily: MONO, fontSize: 20, fontWeight: 700, color: LIGHT.accent }}>
              3 · @phenotyper (Gemini Pro)
            </div>
            <div style={{ fontSize: 25, color: LIGHT.ink, fontWeight: 600, marginTop: 6 }}>
              Extracts meds, RT, labs &amp; biomarkers
            </div>
          </div>
        </div>

        <div style={{ textAlign: 'center', fontSize: 38, color: LIGHT.accent, opacity: c3 }}>→</div>

        {/* 4: @safety-auditor */}
        <div
          style={{
            background: LIGHT.card,
            border: `2px solid ${LIGHT.line}`,
            borderRadius: 22,
            padding: '28px 24px',
            minHeight: 370,
            opacity: c3,
            transform: `translateY(${(1 - c3) * 20}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 21, fontWeight: 700, color: LIGHT.red }}>4 · @safety-auditor</div>
          <div style={{ fontSize: 42, fontWeight: 800, marginTop: 10 }}>Audit R1–R5</div>
          <div style={{ fontSize: 26, color: LIGHT.muted, lineHeight: 1.32, marginTop: 14 }}>
            Deterministic steroid, washout, RT &amp; CTCAE math.
          </div>
        </div>

        <div style={{ textAlign: 'center', fontSize: 38, color: LIGHT.accent, opacity: c4 }}>→</div>

        {/* 5: @verifier */}
        <div
          style={{
            background: LIGHT.card,
            border: `3px solid ${LIGHT.green}`,
            borderRadius: 22,
            padding: '28px 24px',
            minHeight: 370,
            opacity: c4,
            transform: `translateY(${(1 - c4) * 20}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 21, fontWeight: 700, color: LIGHT.green }}>5 · @verifier</div>
          <div style={{ fontSize: 42, fontWeight: 800, marginTop: 10 }}>Rule R6</div>
          <div style={{ fontSize: 26, color: LIGHT.muted, lineHeight: 1.32, marginTop: 14 }}>
            Blocks any claim without exact line substring.
          </div>
        </div>
      </div>
    </SceneIn>
  );
};

/* ── SCENE 3B (DARK /swarm Board, Chip OUTSIDE capture, Zoomed onto Board) ──────────────────── */
const Scene3bSwarmDark: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, D.s3b], [1.18, 1.26], { extrapolateRight: 'clamp' });

  return (
    <SceneIn>
      <TopBar tag="ANTIGRAVITY /SWARM BOARD · LIVE AUDIT" step="04 / 07" />

      {/* Chip sits cleanly ABOVE the capture (Sanad V2 rule) */}
      <div
        style={{
          position: 'absolute',
          left: 80,
          top: 96,
          background: DARK.surface,
          border: `1px solid ${DARK.line}`,
          borderLeft: `6px solid ${DARK.accent}`,
          borderRadius: 10,
          padding: '8px 18px',
          fontSize: 26,
          fontWeight: 700,
        }}
      >
        @safety-auditor (R1): Dexamethasone 4 mg/day → <span style={{ color: DARK.accent }}>26.7 mg/day Prednisone eq</span>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 80,
          top: 158,
          bottom: 118,
          borderRadius: 18,
          overflow: 'hidden',
          border: `2px solid ${DARK.accent}`,
        }}
      >
        <Img
          src={staticFile('shots/ui_03_swarm_board.png')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: 'center 52%',
            transform: `scale(${scale})`,
            transformOrigin: 'center 52%',
          }}
        />
      </div>
    </SceneIn>
  );
};

/* ── SCENE 4 (Workstation Citations -> /judge Trap -> Sign-Off Modal, Chips Outside) ─────────── */
const Scene4Verifier: React.FC = () => {
  const frame = useCurrentFrame();
  const cut1 = 135; // 4.5s -> /judge adversarial trap
  const cut2 = 260; // 8.7s -> SHA-256 Sign-Off modal

  const activeShot =
    frame < cut1
      ? 'shots/ui_02_citation_click.png'
      : frame < cut2
      ? 'shots/ui_05_judge_top.png'
      : 'shots/ui_04_signoff_modal.png';

  const chipText =
    frame < cut1
      ? 'Verdict: CONTRAINDICATED · EHR L26 ↔ Protocol L20 line-anchored'
      : frame < cut2
      ? '/judge Adversarial Probe: UNVERIFIED_CITATION_BLOCKED (Rule R6)'
      : 'Human CRC Gate: 21 CFR Part 11-style SHA-256 Sign-Off Receipt';

  const anchor =
    frame < cut1 ? 'center 55%' : frame < cut2 ? 'center 35%' : 'center 92%';

  const fadeCut =
    frame < cut1
      ? 1
      : frame < cut2
      ? interpolate(frame, [cut1, cut1 + 6], [0.35, 1], { extrapolateRight: 'clamp' })
      : interpolate(frame, [cut2, cut2 + 6], [0.35, 1], { extrapolateRight: 'clamp' });

  const zoom = interpolate(frame, [0, D.s4], [1.14, 1.22], { extrapolateRight: 'clamp' });

  return (
    <SceneIn>
      <TopBar tag="RULE R6 LINE GROUNDING · /judge & CRC SIGN-OFF" step="05 / 07" />

      <div
        style={{
          position: 'absolute',
          left: 80,
          top: 96,
          background: DARK.surface,
          border: `1px solid ${DARK.line}`,
          borderLeft: `6px solid ${frame >= cut1 ? DARK.green : DARK.accent}`,
          borderRadius: 10,
          padding: '8px 18px',
          fontSize: 26,
          fontWeight: 700,
          opacity: fadeCut,
        }}
      >
        {chipText}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 80,
          top: 158,
          bottom: 118,
          borderRadius: 18,
          overflow: 'hidden',
          border: `2px solid ${frame >= cut1 ? DARK.green : DARK.accent}`,
          opacity: fadeCut,
        }}
      >
        <Img
          src={staticFile(activeShot)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            objectPosition: anchor,
            transform: `scale(${zoom})`,
            transformOrigin: anchor,
          }}
        />
      </div>
    </SceneIn>
  );
};

/* ── SCENE 5A (LIGHT Scorecard with Cubic Easing) ────────────────────────────────────────────── */
const Scene5aScorecardLight: React.FC = () => {
  const frame = useCurrentFrame();
  const prog = interpolate(frame, [6, 56], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const bar1 = 100 * prog;
  const bar2 = 47.5 * prog;

  return (
    <SceneIn fromDark theme="light">
      <TopBar tag="VERIFIED BENCHMARK · n = 120 ONCOLOGY COHORT" step="06 / 07" theme="light" />

      <div style={{ position: 'absolute', left: 80, right: 80, top: 122 }}>
        <div style={{ fontSize: 68, fontWeight: 800, letterSpacing: -2 }}>
          100.0% Exact Accuracy <span style={{ color: LIGHT.accent }}>(120 / 120)</span>
        </div>

        <div style={{ marginTop: 32, display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 1450 }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 28, fontWeight: 700, marginBottom: 10 }}>
              <span>TrialSwarm AI (/swarm + R1–R6)</span>
              <span style={{ color: LIGHT.green, fontFamily: MONO }}>{bar1.toFixed(1)}% (0 mismatches)</span>
            </div>
            <div style={{ height: 42, borderRadius: 12, background: LIGHT.line, overflow: 'hidden' }}>
              <div style={{ width: `${bar1}%`, height: '100%', background: LIGHT.green, borderRadius: 12 }} />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 28, fontWeight: 700, marginBottom: 10 }}>
              <span style={{ color: LIGHT.muted }}>Naive Single-Prompt Baseline</span>
              <span style={{ color: LIGHT.red, fontFamily: MONO }}>{bar2.toFixed(1)}% (30.0% specificity)</span>
            </div>
            <div style={{ height: 42, borderRadius: 12, background: LIGHT.line, overflow: 'hidden' }}>
              <div style={{ width: `${bar2}%`, height: '100%', background: LIGHT.red, borderRadius: 12 }} />
            </div>
          </div>
        </div>

        <div style={{ marginTop: 38, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20 }}>
          {[
            ['R1 Steroid', '15 / 15'],
            ['R2–R3 Washout & RT', '30 / 30'],
            ['R4 CTCAE Organ', '15 / 15'],
            ['R5 Reflex Biomarker', '30 / 30'],
          ].map(([k, v]) => (
            <div
              key={k}
              style={{
                background: LIGHT.card,
                border: `2px solid ${LIGHT.line}`,
                borderRadius: 16,
                padding: '20px 24px',
              }}
            >
              <div style={{ fontSize: 22, color: LIGHT.muted, fontWeight: 700 }}>{k}</div>
              <div style={{ fontSize: 40, fontWeight: 800, color: LIGHT.green, marginTop: 6 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>
    </SceneIn>
  );
};

/* ── SCENE 5B (DARK End Card) ───────────────────────────────────────────────────────────────── */
const Scene5bEndDark: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const ctaIn = spring({ frame, fps, config: { damping: 20 } });

  return (
    <SceneIn>
      <TopBar tag="BERKELEY x DEEPMIND · BUILT, SHIPPED & LIVE" step="07 / 07" />

      <div
        style={{
          position: 'absolute',
          left: 80,
          right: 80,
          top: 190,
          opacity: ctaIn,
          transform: `translateY(${(1 - ctaIn) * 20}px)`,
        }}
      >
        <div style={{ fontSize: 92, fontWeight: 800, letterSpacing: -2.5 }}>
          TrialSwarm <span style={{ color: DARK.accent }}>AI</span>
        </div>
        <div style={{ fontSize: 34, color: DARK.muted, marginTop: 14 }}>
          Physician-Signed Oncology Trial Safety Swarm · Dr. Ahmed Zayed, MB BCh
        </div>

        <div style={{ marginTop: 48, display: 'flex', gap: 24 }}>
          {[
            ['$0.0000', 'Offline Compute'],
            ['4.08 ms', 'Mean Latency'],
            ['16 / 16', 'CI Tests Passing'],
          ].map(([v, l]) => (
            <div
              key={l}
              style={{
                background: DARK.surface,
                border: `1.5px solid ${DARK.line}`,
                borderRadius: 16,
                padding: '22px 30px',
                minWidth: 230,
              }}
            >
              <div style={{ fontSize: 42, fontWeight: 800, color: DARK.accent }}>{v}</div>
              <div style={{ fontSize: 22, color: DARK.muted, marginTop: 4 }}>{l}</div>
            </div>
          ))}

          <div
            style={{
              flex: 1,
              background: 'rgba(232,163,61,0.14)',
              border: `2px solid ${DARK.accent}`,
              borderRadius: 16,
              padding: '22px 30px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, color: DARK.accent, letterSpacing: 1 }}>
              TRY LIVE NOW (ZERO LOGIN)
            </div>
            <div style={{ fontFamily: MONO, fontSize: 25, fontWeight: 700, marginTop: 8 }}>
              https://ahmedadel7887--trialswarm-ai-web.us-east.modal.run/
            </div>
          </div>
        </div>
      </div>
    </SceneIn>
  );
};

/* Global Captions mounted ONCE at root (zero caption collisions) */
const GLOBAL_CUES = [
  { from: 0, to: 135, text: 'An oncology coordinator spends four hours per pre-screen—' },
  { from: 135, to: 318, text: 'and one missed steroid conversion triggers a dangerous IRB protocol deviation.' },
  { from: F.s2, to: F.s2 + 125, text: 'Marcus Vance takes Dexamethasone two milligrams BID.' },
  { from: F.s2 + 125, to: F.s2 + 328, text: 'Naive LLMs see four milligrams, check the ten-milligram ceiling, and falsely clear him.' },
  { from: F.s3a, to: F.s3a + 120, text: 'TrialSwarm coordinates five agents on an Antigravity swarm.' },
  { from: F.s3a + 120, to: F.s3b, text: 'Extractor and Phenotyper parse protocol and EHR in parallel.' },
  { from: F.s3b, to: F.s4 - 4, text: 'Rule R1 converts Dexamethasone to 26.7 milligrams Prednisone equivalent.' },
  { from: F.s4, to: F.s4 + 135, text: 'Verdict: Contraindicated. The Verifier enforces Rule R6:' },
  { from: F.s4 + 135, to: F.s5a - 4, text: 'every claim is line-anchored to source text, blocking hallucinations before CRC sign-off.' },
  { from: F.s5a, to: F.s5b, text: 'One hundred percent accuracy on one hundred twenty cases.' },
  { from: F.s5b, to: TOTAL_FRAMES, text: 'Zero-cost deterministic compute. Built, shipped, and live.' },
];

const RootCaptions: React.FC = () => {
  const frame = useCurrentFrame();
  const cue = GLOBAL_CUES.find((c) => frame >= c.from && frame < c.to);
  if (!cue) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 80,
        right: 80,
        bottom: 26,
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: 'rgba(13, 17, 23, 0.94)',
          border: `1px solid ${DARK.line}`,
          borderLeft: `6px solid ${DARK.accent}`,
          borderRadius: 12,
          padding: '12px 24px',
          fontFamily: SANS,
          fontSize: 30,
          lineHeight: 1.25,
          color: DARK.text,
          maxWidth: 1680,
          boxShadow: '0 12px 32px rgba(0,0,0,0.45)',
        }}
      >
        {cue.text}
      </div>
    </div>
  );
};

const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        bottom: 0,
        height: 6,
        width: `${(100 * (frame + 1)) / TOTAL_FRAMES}%`,
        background: DARK.accent,
      }}
    />
  );
};

export const TrialSwarmPitch: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: DARK.bg }}>
      <Sequence from={F.s1} durationInFrames={D.s1}>
        <Audio src={staticFile('audio/pitch_01_hook.mp3')} />
        <Scene1Hook />
      </Sequence>

      <Sequence from={F.s2} durationInFrames={D.s2}>
        <Audio src={staticFile('audio/pitch_02_trap.mp3')} />
        <Scene2Trap />
      </Sequence>

      <Sequence from={F.s3a} durationInFrames={D.s3a + D.s3b}>
        <Audio src={staticFile('audio/pitch_03_swarm.mp3')} />
      </Sequence>
      <Sequence from={F.s3a} durationInFrames={D.s3a}>
        <Scene3aWorkflowLight />
      </Sequence>
      <Sequence from={F.s3b} durationInFrames={D.s3b}>
        <Scene3bSwarmDark />
      </Sequence>

      <Sequence from={F.s4} durationInFrames={D.s4}>
        <Audio src={staticFile('audio/pitch_04_verifier.mp3')} />
        <Scene4Verifier />
      </Sequence>

      <Sequence from={F.s5a} durationInFrames={D.s5a + D.s5b}>
        <Audio src={staticFile('audio/pitch_05_close.mp3')} />
      </Sequence>
      <Sequence from={F.s5a} durationInFrames={D.s5a}>
        <Scene5aScorecardLight />
      </Sequence>
      <Sequence from={F.s5b} durationInFrames={D.s5b}>
        <Scene5bEndDark />
      </Sequence>

      <RootCaptions />
      <ProgressBar />
    </AbsoluteFill>
  );
};
