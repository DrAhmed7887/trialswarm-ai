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

export const DEMO_FPS = 30;

// Strictly sequential durations matching video/demo/assets/audio/vo/durations.json
// Total VO = 177.63s; with 8f breathing gaps = 5388 frames = 179.60s (2m 59.6s)
export const DEMO_SCENES = {
  s1a: 557, // 18.57s -> cuts right as "When AI guesses on eligibility..." starts
  s1b: 280, // 9.33s  (total s1 = 837f)
  s2a: 453, // 15.10s -> cuts right as "Then, Safety-Auditor executes..." starts
  s2b: 372, // 12.40s (total s2 = 825f)
  s3a: 494, // 16.47s -> cuts right as "But TrialSwarm's Rule R1..." starts
  s3b: 320, // 10.67s (total s3 = 814f)
  s4a: 441, // 14.70s -> cuts right as "And Rule R2 catches another..." starts
  s4b: 362, // 12.07s (total s4 = 803f)
  s5: 670, // 22.33s (demo_05_r6_adversarial_trap: 662f + 8f gap)
  s6: 730, // 24.33s (demo_06_cohort_scenarios: 722f + 8f gap)
  s7a: 422, // 14.07s -> cuts right as "Clinical coordinators then execute..." starts
  s7b: 287, // 9.57s  (total s7 = 709f)
} as const;

const S1_START = 0;
const S1_DUR = DEMO_SCENES.s1a + DEMO_SCENES.s1b; // 837
const S2_START = S1_START + S1_DUR; // 837
const S2_DUR = DEMO_SCENES.s2a + DEMO_SCENES.s2b; // 825
const S3_START = S2_START + S2_DUR; // 1662
const S3_DUR = DEMO_SCENES.s3a + DEMO_SCENES.s3b; // 814
const S4_START = S3_START + S3_DUR; // 2476
const S4_DUR = DEMO_SCENES.s4a + DEMO_SCENES.s4b; // 803
const S5_START = S4_START + S4_DUR; // 3279
const S5_DUR = DEMO_SCENES.s5; // 670
const S6_START = S5_START + S5_DUR; // 3949
const S6_DUR = DEMO_SCENES.s6; // 730
const S7_START = S6_START + S6_DUR; // 4679
const S7_DUR = DEMO_SCENES.s7a + DEMO_SCENES.s7b; // 709

export const DEMO_TOTAL_FRAMES = S7_START + S7_DUR; // 5388 (179.60s)

const COLORS = {
  darkBg: '#0D1117',
  darkCard: '#161B22',
  darkBorder: '#30363D',
  darkInk: '#F0F6FC',
  darkMuted: '#9BA3B0',
  lightBg: '#F6F4EF',
  lightCard: '#FFFFFF',
  lightBorder: '#E5E0D5',
  lightInk: '#1A1E24',
  lightMuted: '#57606A',
  gold: '#E8A33D',
  terracotta: '#C84B31',
  red: '#DC2626',
  redSoft: '#F87171',
  green: '#0F9D78',
  greenSoft: '#34D399',
  blue: '#38BDF8',
  purple: '#A78BFA',
};

const FONT_SANS =
  'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const FONT_MONO =
  'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace';

interface CaptionCue {
  start: number;
  end: number;
  text: string;
}

const DEMO_CAPTIONS: CaptionCue[] = [
  // s1 (0..837) — synced to ffmpeg silencedetect
  { start: 0, end: 118, text: 'Clinical trial eligibility screening is broken.' },
  {
    start: 118,
    end: 327,
    text: 'While large language models can parse free text, they fail on strict medical calculations:',
  },
  {
    start: 327,
    end: 557,
    text: 'glucocorticoid potency conversions, relative washout windows, and CTCAE laboratory thresholds.',
  },
  {
    start: 557,
    end: 695,
    text: 'When AI guesses on eligibility, patients face lethal toxicity,',
  },
  {
    start: 695,
    end: 829,
    text: 'and clinical trials suffer devastating protocol violations.',
  },
  // s2 (837..1662)
  {
    start: 837,
    end: 1091,
    text: 'TrialSwarm AI solves this through a multi-agent Antigravity /swarm coupled with deterministic clinical verifiers.',
  },
  {
    start: 1091,
    end: 1290,
    text: '@extractor and @phenotyper parse trial protocols and electronic health records in parallel.',
  },
  {
    start: 1290,
    end: 1471,
    text: 'Then @safety-auditor executes deterministic clinical rules R1 through R5,',
  },
  {
    start: 1471,
    end: 1654,
    text: 'grounded in active oncology trials from ClinicalTrials.gov and peer-reviewed literature.',
  },
  // s3 (1662..2476)
  {
    start: 1662,
    end: 1858,
    text: "Let's examine patient Marcus Vance, screened against the Mirati KRYSTAL-7 protocol.",
  },
  {
    start: 1858,
    end: 2156,
    text: 'A naive language model sees 4 mg daily Dexamethasone, compares it to the 10 mg ceiling, and marks him eligible.',
  },
  {
    start: 2156,
    end: 2379,
    text: "But TrialSwarm's Rule R1 converts Dexamethasone to 26.7 mg Prednisone equivalent,",
  },
  {
    start: 2379,
    end: 2468,
    text: 'triggering an immediate Contraindicated verdict.',
  },
  // s4 (2476..3279)
  {
    start: 2476,
    end: 2648,
    text: "On the Antigravity /swarm board, every agent's contribution is transparently logged.",
  },
  {
    start: 2648,
    end: 2801,
    text: '@extractor extracts 10 criteria with verbatim line citations.',
  },
  {
    start: 2801,
    end: 2917,
    text: '@phenotyper grounds 14 clinical facts.',
  },
  {
    start: 2917,
    end: 3175,
    text: 'And Rule R2 catches another critical trap: prior anti-LAG-3 therapy ending only 19 days ago,',
  },
  {
    start: 3175,
    end: 3271,
    text: 'violating the required 28-day washout.',
  },
  // s5 (3279..3949)
  {
    start: 3279,
    end: 3460,
    text: 'In the /judge console, we test our system against adversarial hallucination.',
  },
  {
    start: 3460,
    end: 3768,
    text: 'When an attacker or faulty model injects a fabricated quote claiming 0 mg steroids, Rule R6 instantly rejects it.',
  },
  {
    start: 3768,
    end: 3941,
    text: 'If a claim is not an exact substring of the cited text lines, it is deterministically blocked.',
  },
  // s6 (3949..4679)
  {
    start: 3949,
    end: 4083,
    text: 'TrialSwarm handles diverse oncology profiles seamlessly.',
  },
  {
    start: 4083,
    end: 4190,
    text: 'Patient 101 clears all criteria as Eligible.',
  },
  {
    start: 4190,
    end: 4391,
    text: 'Patient 103 is Contraindicated due to thoracic radiation and grade-2 liver enzymes.',
  },
  {
    start: 4391,
    end: 4671,
    text: 'And Patient 104, with a pending EGFR and ALK panel, is safely routed to Needs Human Review.',
  },
  // s7 (4679..5388)
  {
    start: 4679,
    end: 4973,
    text: 'Across 120 synthetic oncology cases, TrialSwarm achieved 100% accuracy and 0 mismatches,',
  },
  {
    start: 4973,
    end: 5101,
    text: 'compared to 47.5% for the naive baseline.',
  },
  {
    start: 5101,
    end: 5380,
    text: 'Clinical coordinators execute SHA-256 digital sign-offs, creating a tamper-evident audit trail ready for FDA inspection.',
  },
];

const SceneIn: React.FC<{
  children: React.ReactNode;
  dark?: boolean;
  fromDark?: boolean;
}> = ({ children, dark = true, fromDark = false }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const translateY = fromDark
    ? interpolate(frame, [0, 12], [18, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: Easing.out(Easing.cubic),
      })
    : 0;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: dark ? COLORS.darkBg : COLORS.lightBg,
        color: dark ? COLORS.darkInk : COLORS.lightInk,
        fontFamily: FONT_SANS,
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const SceneBadge: React.FC<{
  label: string;
  step: string;
  dark?: boolean;
}> = ({ label, step, dark = true }) => (
  <div
    style={{
      position: 'absolute',
      top: 40,
      left: 72,
      right: 72,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 10,
    }}
  >
    <div
      style={{
        padding: '8px 18px',
        borderRadius: 999,
        border: `1.5px solid ${dark ? COLORS.gold : COLORS.terracotta}`,
        backgroundColor: dark
          ? 'rgba(232,163,61,0.10)'
          : 'rgba(200,75,49,0.08)',
        color: dark ? COLORS.gold : COLORS.terracotta,
        fontSize: 18,
        fontWeight: 700,
        letterSpacing: '0.07em',
        textTransform: 'uppercase',
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontFamily: FONT_MONO,
        fontSize: 18,
        fontWeight: 600,
        color: dark ? COLORS.darkMuted : COLORS.lightMuted,
      }}
    >
      {step}
    </div>
  </div>
);

const RootCaptions: React.FC = () => {
  const frame = useCurrentFrame();
  const active = DEMO_CAPTIONS.find((c) => frame >= c.start && frame < c.end);
  if (!active) return null;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        zIndex: 50,
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(13, 17, 23, 0.90)',
          border: '1px solid rgba(255,255,255,0.14)',
          borderLeft: `4px solid ${COLORS.gold}`,
          borderRadius: 12,
          padding: '11px 28px',
          maxWidth: 1320,
          boxShadow: '0 8px 28px rgba(0,0,0,0.38)',
        }}
      >
        <div
          style={{
            color: '#F8FAFC',
            fontSize: 25,
            fontWeight: 600,
            fontFamily: FONT_SANS,
            textAlign: 'center',
            lineHeight: 1.32,
          }}
        >
          {active.text}
        </div>
      </div>
    </div>
  );
};

const RootProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const pct = Math.min(100, (frame / DEMO_TOTAL_FRAMES) * 100);
  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: 6,
        backgroundColor: 'rgba(128,128,128,0.22)',
        zIndex: 60,
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: '100%',
          backgroundColor: COLORS.gold,
        }}
      />
    </div>
  );
};

// Scene 1A (Dark, 390f): The Broken Screening Baseline + 120-Case Grid
const Scene1aProblemHook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 120 },
  });
  const revealCount = Math.floor(
    interpolate(frame, [20, 140], [0, 120], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );
  const missCount = Math.floor(
    interpolate(frame, [40, 150], [0, 63], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  const traps = [
    { label: 'Glucocorticoid Potency', delay: 320 },
    { label: 'Relative Washout Windows', delay: 400 },
    { label: 'CTCAE Lab Thresholds', delay: 452 },
  ];

  return (
    <SceneIn dark>
      <SceneBadge label="01 · Clinical Screening Crisis" step="01 / 12" dark />
      <div
        style={{
          display: 'flex',
          padding: '124px 72px 96px',
          gap: 56,
          height: '100%',
          alignItems: 'center',
          boxSizing: 'border-box',
        }}
      >
        <div style={{ flex: 1.08 }}>
          <h1
            style={{
              fontSize: 66,
              fontWeight: 800,
              lineHeight: 1.07,
              margin: 0,
              transform: `translateY(${(1 - titleSpring) * 20}px)`,
              opacity: titleSpring,
            }}
          >
            Clinical Trial Screening{' '}
            <span style={{ color: COLORS.redSoft }}>Is Broken.</span>
          </h1>
          <p
            style={{
              fontSize: 27,
              color: COLORS.darkMuted,
              marginTop: 22,
              lineHeight: 1.4,
            }}
          >
            Single-prompt LLMs parse free text fluently—yet fail{' '}
            <strong style={{ color: COLORS.darkInk }}>52.5%</strong> of
            high-stakes oncology eligibility traps.
          </p>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              marginTop: 28,
            }}
          >
            {traps.map((t, idx) => {
              const p = interpolate(frame, [t.delay, t.delay + 18], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
              return (
                <div
                  key={t.label}
                  style={{
                    opacity: p,
                    transform: `translateX(${(1 - p) * -20}px)`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '14px 20px',
                    borderRadius: 12,
                    backgroundColor: COLORS.darkCard,
                    border: `1px solid ${COLORS.darkBorder}`,
                    borderLeft: `4px solid ${COLORS.redSoft}`,
                  }}
                >
                  <span
                    style={{
                      fontFamily: FONT_MONO,
                      color: COLORS.gold,
                      fontWeight: 800,
                      fontSize: 18,
                    }}
                  >
                    0{idx + 1}
                  </span>
                  <span style={{ fontSize: 22, fontWeight: 700 }}>
                    {t.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div
          style={{
            flex: 0.92,
            backgroundColor: COLORS.darkCard,
            border: `1.5px solid ${COLORS.darkBorder}`,
            borderRadius: 20,
            padding: 32,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 20,
              whiteSpace: 'nowrap',
            }}
          >
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 18,
                fontWeight: 700,
                color: COLORS.darkMuted,
              }}
            >
              BENCHMARK COHORT (n = 120)
            </span>
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 18,
                fontWeight: 700,
                color: COLORS.redSoft,
              }}
            >
              NAIVE LLM MISSES: {missCount}
            </span>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(12, 1fr)',
              gap: 8,
            }}
          >
            {Array.from({ length: 120 }).map((_, i) => {
              const lit = i < revealCount;
              const isMiss = i >= 57;
              return (
                <div
                  key={i}
                  style={{
                    height: 28,
                    borderRadius: 6,
                    backgroundColor: !lit
                      ? '#21262D'
                      : isMiss
                      ? COLORS.red
                      : COLORS.green,
                    opacity: lit ? 0.95 : 0.4,
                  }}
                />
              );
            })}
          </div>
          <div
            style={{
              marginTop: 20,
              display: 'flex',
              justifyContent: 'space-between',
              fontFamily: FONT_MONO,
              fontSize: 16,
              color: COLORS.darkMuted,
            }}
          >
            <span>Naive LLM: 47.5% (57/120)</span>
            <span style={{ color: COLORS.greenSoft }}>
              TrialSwarm Target: 100.0%
            </span>
          </div>
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 1B (Light, 447f): The 3 Lethal Traps & Protocol Violation Consequence
const Scene1bTrapsDetail: React.FC = () => {
  const frame = useCurrentFrame();

  const cards = [
    {
      rule: 'RULE R1 · STEROID POTENCY',
      naive: 'Dexamethasone 4 mg <= 10 mg -> PASS',
      reality: '4 mg × 6.67 = 26.7 mg Prednisone eq',
      consequence: 'Severe Immunosuppression Risk',
      delay: 6,
    },
    {
      rule: 'RULE R2 · WASHOUT WINDOW',
      naive: 'Prior anti-LAG-3 noted -> PASS',
      reality: '19 days elapsed < 28-day required',
      consequence: 'Overlapping Drug Toxicity',
      delay: 36,
    },
    {
      rule: 'RULE R4 · CTCAE ORGAN GRADE',
      naive: 'AST 142 / ALT 156 -> PASS',
      reality: 'Grade 2 Hepatotoxicity (> 3× ULN)',
      consequence: 'IRB Protocol Deviation',
      delay: 66,
    },
  ];

  const stampOpacity = interpolate(frame, [115, 138], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const stampScale = interpolate(frame, [115, 138], [1.15, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="02 · Why Single-Prompt LLMs Fail"
        step="02 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '124px 72px 110px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 54, fontWeight: 800, margin: 0 }}>
            Three Calculations AI Cannot Afford to Guess
          </h2>
          <p
            style={{
              fontSize: 25,
              color: COLORS.lightMuted,
              marginTop: 12,
              marginBottom: 0,
            }}
          >
            Each missed conversion puts a patient at risk and triggers an IRB
            audit failure.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 28 }}>
          {cards.map((c) => {
            const p = interpolate(frame, [c.delay, c.delay + 22], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.out(Easing.cubic),
            });
            return (
              <div
                key={c.rule}
                style={{
                  flex: 1,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 24}px)`,
                  backgroundColor: COLORS.lightCard,
                  border: `1.5px solid ${COLORS.lightBorder}`,
                  borderTop: `6px solid ${COLORS.terracotta}`,
                  borderRadius: 18,
                  padding: 28,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.05)',
                }}
              >
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 15,
                    fontWeight: 800,
                    color: COLORS.terracotta,
                    marginBottom: 16,
                  }}
                >
                  {c.rule}
                </div>
                <div
                  style={{
                    padding: '12px 14px',
                    borderRadius: 10,
                    backgroundColor: '#FEF2F2',
                    border: '1px solid #FECACA',
                    fontFamily: FONT_MONO,
                    fontSize: 16,
                    color: '#991B1B',
                    marginBottom: 14,
                  }}
                >
                  Naive LLM: {c.naive}
                </div>
                <div
                  style={{
                    fontSize: 23,
                    fontWeight: 800,
                    color: COLORS.lightInk,
                    marginBottom: 10,
                  }}
                >
                  {c.reality}
                </div>
                <div style={{ fontSize: 18, color: COLORS.lightMuted }}>
                  Risk: <strong>{c.consequence}</strong>
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            opacity: stampOpacity,
            transform: `scale(${stampScale})`,
            padding: '18px 28px',
            borderRadius: 14,
            backgroundColor: '#FEE2E2',
            border: `2px solid ${COLORS.red}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span
            style={{ fontSize: 24, fontWeight: 800, color: '#991B1B' }}
          >
            RESULT OF PROBABILISTIC GUESSING: LETHAL TOXICITY &amp; PROTOCOL
            VIOLATION
          </span>
          <span
            style={{
              fontFamily: FONT_MONO,
              fontSize: 18,
              fontWeight: 800,
              color: '#FFFFFF',
              backgroundColor: COLORS.red,
              padding: '8px 16px',
              borderRadius: 8,
            }}
          >
            UNACCEPTABLE IN ONCOLOGY
          </span>
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 2A (Dark, 420f): How Antigravity /swarm Solved It — Animated Parallel Flow
const Scene2aSwarmFlow: React.FC = () => {
  const frame = useCurrentFrame();

  const dashOffset = -(frame * 2.5);
  const pulseX1 = interpolate(frame % 75, [0, 75], [0, 1]);
  const pulseX2 = interpolate((frame + 35) % 75, [0, 75], [0, 1]);

  const nodes = [
    {
      id: '@extractor',
      role: 'Protocol Parser',
      out: '10 Criteria · Line-Cited',
      color: COLORS.blue,
      y: 120,
      delay: 40,
    },
    {
      id: '@phenotyper',
      role: 'EHR Grounder',
      out: '14 Facts · Line-Cited',
      color: COLORS.purple,
      y: 340,
      delay: 65,
    },
  ];

  const downstream = [
    {
      id: '@safety-auditor',
      role: 'Rules R1–R5 Engine',
      out: 'Deterministic Math',
      color: COLORS.gold,
      delay: 130,
    },
    {
      id: '@citation-verifier',
      role: 'Rule R6 Blocker',
      out: 'Exact Substring Gate',
      color: COLORS.greenSoft,
      delay: 195,
    },
    {
      id: '@clinical-signer',
      role: 'SHA-256 Sign-Off',
      out: 'FDA-Ready Audit',
      color: '#F472B6',
      delay: 255,
    },
  ];

  return (
    <SceneIn dark>
      <SceneBadge
        label="03 · Built with Antigravity /swarm"
        step="03 / 12"
        dark
      />
      <div
        style={{
          padding: '116px 72px 100px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 52, fontWeight: 800, margin: 0 }}>
            How <span style={{ color: COLORS.gold }}>Antigravity /swarm</span>{' '}
            Splits &amp; Verifies the Work
          </h2>
          <p
            style={{
              fontSize: 23,
              color: COLORS.darkMuted,
              marginTop: 10,
              marginBottom: 0,
            }}
          >
            Instead of one monolithic prompt guessing, 5 specialized agents
            collaborate in parallel and pass deterministic gates.
          </p>
        </div>

        {/* Animated SVG + Card Flow Diagram */}
        <div
          style={{
            position: 'relative',
            height: 490,
            width: '100%',
            backgroundColor: COLORS.darkCard,
            border: `1.5px solid ${COLORS.darkBorder}`,
            borderRadius: 22,
            overflow: 'hidden',
          }}
        >
          <svg
            width="1776"
            height="490"
            viewBox="0 0 1776 490"
            style={{ position: 'absolute', inset: 0 }}
          >
            {/* Input -> Parallel Workers */}
            <path
              d="M 280 245 C 360 245, 360 150, 440 150"
              fill="none"
              stroke={COLORS.blue}
              strokeWidth="3.5"
              strokeDasharray="10 8"
              strokeDashoffset={dashOffset}
            />
            <path
              d="M 280 245 C 360 245, 360 350, 440 350"
              fill="none"
              stroke={COLORS.purple}
              strokeWidth="3.5"
              strokeDasharray="10 8"
              strokeDashoffset={dashOffset}
            />
            {/* Parallel Workers -> Safety Auditor */}
            <path
              d="M 790 150 C 860 150, 860 245, 920 245"
              fill="none"
              stroke={COLORS.gold}
              strokeWidth="3.5"
              strokeDasharray="10 8"
              strokeDashoffset={dashOffset}
            />
            <path
              d="M 790 350 C 860 350, 860 245, 920 245"
              fill="none"
              stroke={COLORS.gold}
              strokeWidth="3.5"
              strokeDasharray="10 8"
              strokeDashoffset={dashOffset}
            />
            {/* Downstream sequential gates */}
            <line
              x1="1180"
              y1="245"
              x2="1235"
              y2="245"
              stroke={COLORS.greenSoft}
              strokeWidth="4"
              strokeDasharray="8 6"
              strokeDashoffset={dashOffset}
            />
            <line
              x1="1475"
              y1="245"
              x2="1525"
              y2="245"
              stroke="#F472B6"
              strokeWidth="4"
              strokeDasharray="8 6"
              strokeDashoffset={dashOffset}
            />

            {/* Moving data packets */}
            <circle
              cx={280 + pulseX1 * 160}
              cy={245 - pulseX1 * 95}
              r="7"
              fill={COLORS.blue}
            />
            <circle
              cx={280 + pulseX2 * 160}
              cy={245 + pulseX2 * 105}
              r="7"
              fill={COLORS.purple}
            />
            <circle
              cx={790 + pulseX1 * 130}
              cy={150 + pulseX1 * 95}
              r="7"
              fill={COLORS.gold}
            />
          </svg>

          {/* Left Input Box */}
          <div
            style={{
              position: 'absolute',
              left: 36,
              top: 155,
              width: 244,
              padding: '22px 20px',
              borderRadius: 16,
              backgroundColor: '#1F2937',
              border: `1.5px solid ${COLORS.darkBorder}`,
            }}
          >
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 13,
                color: COLORS.gold,
                fontWeight: 700,
              }}
            >
              LIVE INPUTS
            </div>
            <div style={{ fontSize: 20, fontWeight: 800, marginTop: 8 }}>
              Protocol + Patient EHR
            </div>
            <div
              style={{
                fontSize: 15,
                color: COLORS.darkMuted,
                marginTop: 8,
                lineHeight: 1.4,
              }}
            >
              ClinicalTrials.gov v2 + raw clinical notes
            </div>
          </div>

          {/* Parallel Agents */}
          {nodes.map((n) => {
            const p = interpolate(frame, [n.delay, n.delay + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={n.id}
                style={{
                  position: 'absolute',
                  left: 440,
                  top: n.y - 25,
                  width: 350,
                  padding: '20px 22px',
                  borderRadius: 16,
                  backgroundColor: '#131A24',
                  border: `2px solid ${n.color}`,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 16}px)`,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span
                    style={{
                      fontFamily: FONT_MONO,
                      fontSize: 20,
                      fontWeight: 800,
                      color: n.color,
                    }}
                  >
                    {n.id}
                  </span>
                  <span
                    style={{
                      fontFamily: FONT_MONO,
                      fontSize: 13,
                      padding: '3px 9px',
                      borderRadius: 999,
                      backgroundColor: 'rgba(255,255,255,0.08)',
                      color: COLORS.darkInk,
                    }}
                  >
                    PARALLEL
                  </span>
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 6 }}>
                  {n.role}
                </div>
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 15,
                    color: COLORS.darkMuted,
                    marginTop: 6,
                  }}
                >
                  {n.out}
                </div>
              </div>
            );
          })}

          {/* Downstream Deterministic Gates */}
          {downstream.map((d, idx) => {
            const leftPositions = [920, 1235, 1525];
            const widths = [260, 240, 225];
            const p = interpolate(frame, [d.delay, d.delay + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={d.id}
                style={{
                  position: 'absolute',
                  left: leftPositions[idx],
                  top: 158,
                  width: widths[idx],
                  padding: '20px 18px',
                  borderRadius: 16,
                  backgroundColor: '#131A24',
                  border: `2px solid ${d.color}`,
                  opacity: p,
                  transform: `scale(${0.94 + p * 0.06})`,
                }}
              >
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 17,
                    fontWeight: 800,
                    color: d.color,
                  }}
                >
                  {d.id}
                </div>
                <div style={{ fontSize: 19, fontWeight: 800, marginTop: 8 }}>
                  {d.role}
                </div>
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 14,
                    color: COLORS.darkMuted,
                    marginTop: 8,
                  }}
                >
                  {d.out}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 2B (Light, 405f): Deterministic Rules R1-R5 Cascade
const Scene2bRulesCascade: React.FC = () => {
  const frame = useCurrentFrame();
  const rules = [
    {
      code: 'R1',
      title: 'Steroid Potency',
      desc: 'Prednisone equivalent conversion (0.75 mg Dex = 5 mg Pred)',
    },
    {
      code: 'R2',
      title: 'Systemic Washout',
      desc: 'Exact date delta >= 28 days for prior anti-LAG-3 / chemo',
    },
    {
      code: 'R3',
      title: 'Thoracic RT Gate',
      desc: 'Minimum 180-day clearance post-thoracic radiotherapy',
    },
    {
      code: 'R4',
      title: 'CTCAE v5.0 Labs',
      desc: 'AST / ALT / Bilirubin / ANC / CrCl graded deterministically',
    },
    {
      code: 'R5',
      title: 'Reflex Biomarker',
      desc: 'Unrecorded PD-L1 or EGFR/ALK -> NEEDS_HUMAN_REVIEW',
    },
  ];

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="04 · Physician-Signed Rules R1–R5"
        step="04 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '122px 72px 110px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 52, fontWeight: 800, margin: 0 }}>
            Five Deterministic Clinical Gates
          </h2>
          <p
            style={{
              fontSize: 23,
              color: COLORS.lightMuted,
              marginTop: 10,
              marginBottom: 0,
            }}
          >
            Grounded in active ClinicalTrials.gov oncology protocols and
            verified by physician sign-off.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {rules.map((r, i) => {
            const p = interpolate(frame, [i * 38, i * 38 + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.out(Easing.cubic),
            });
            return (
              <div
                key={r.code}
                style={{
                  opacity: p,
                  transform: `translateX(${(1 - p) * 28}px)`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 24,
                  padding: '18px 26px',
                  borderRadius: 14,
                  backgroundColor: COLORS.lightCard,
                  border: `1.5px solid ${COLORS.lightBorder}`,
                  boxShadow: '0 4px 14px rgba(0,0,0,0.04)',
                }}
              >
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 22,
                    fontWeight: 800,
                    color: '#FFFFFF',
                    backgroundColor: COLORS.green,
                    padding: '8px 16px',
                    borderRadius: 10,
                    minWidth: 56,
                    textAlign: 'center',
                  }}
                >
                  {r.code}
                </div>
                <div style={{ width: 260, fontSize: 23, fontWeight: 800 }}>
                  {r.title}
                </div>
                <div style={{ flex: 1, fontSize: 21, color: COLORS.lightMuted }}>
                  {r.desc}
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            display: 'flex',
            gap: 16,
            fontFamily: FONT_MONO,
            fontSize: 17,
            fontWeight: 700,
            color: COLORS.lightMuted,
          }}
        >
          <span>GROUNDED PROTOCOLS:</span>
          <span style={{ color: COLORS.terracotta }}>NCT04613596 (KRYSTAL-7)</span>
          <span>·</span>
          <span style={{ color: COLORS.terracotta }}>NCT04787042</span>
          <span>·</span>
          <span style={{ color: COLORS.terracotta }}>NCT06890598</span>
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 3A (Dark, 390f): PT-102 Marcus Vance Steroid Potency Trap
const Scene3aPt102Trap: React.FC = () => {
  const frame = useCurrentFrame();
  const naiveIn = interpolate(frame, [90, 115], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const swarmIn = interpolate(frame, [200, 225], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneIn dark>
      <SceneBadge
        label="05 · Case PT-102 (Marcus Vance)"
        step="05 / 12"
        dark
      />
      <div
        style={{
          padding: '124px 72px 110px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 54, fontWeight: 800, margin: 0 }}>
            Protocol NCT04613596 · Mirati KRYSTAL-7
          </h2>
          <p
            style={{
              fontSize: 24,
              color: COLORS.darkMuted,
              marginTop: 10,
              marginBottom: 0,
            }}
          >
            Excludes systemic corticosteroids &gt; 10 mg/day Prednisone
            equivalent.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 36 }}>
          <div
            style={{
              flex: 1,
              backgroundColor: COLORS.darkCard,
              border: `1.5px solid ${COLORS.darkBorder}`,
              borderRadius: 18,
              padding: 32,
            }}
          >
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 16,
                color: COLORS.gold,
                fontWeight: 700,
              }}
            >
              EHR LINE 26 · MEDICATIONS
            </div>
            <div style={{ fontSize: 38, fontWeight: 800, marginTop: 14 }}>
              Dexamethasone 2 mg BID
            </div>
            <div
              style={{
                fontSize: 24,
                color: COLORS.darkMuted,
                marginTop: 10,
              }}
            >
              Raw total = <strong style={{ color: COLORS.darkInk }}>4.0 mg/day</strong>
            </div>
          </div>

          <div
            style={{
              flex: 1,
              opacity: naiveIn,
              transform: `translateY(${(1 - naiveIn) * 18}px)`,
              backgroundColor: COLORS.darkCard,
              border: `2px solid ${COLORS.red}`,
              borderRadius: 18,
              padding: 32,
            }}
          >
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 16,
                color: COLORS.redSoft,
                fontWeight: 700,
              }}
            >
              NAIVE SINGLE-PROMPT LLM
            </div>
            <div
              style={{
                display: 'inline-block',
                marginTop: 14,
                padding: '10px 20px',
                borderRadius: 10,
                backgroundColor: 'rgba(220,38,38,0.18)',
                border: `1px solid ${COLORS.redSoft}`,
                color: COLORS.redSoft,
                fontSize: 28,
                fontWeight: 800,
              }}
            >
              ELIGIBLE (FALSE PASS)
            </div>
            <div
              style={{
                fontSize: 22,
                color: COLORS.darkMuted,
                marginTop: 14,
              }}
            >
              Compares <strong>4.0 mg &lt;= 10 mg</strong> without steroid
              potency conversion.
            </div>
          </div>
        </div>

        <div
          style={{
            opacity: swarmIn,
            transform: `translateY(${(1 - swarmIn) * 18}px)`,
            padding: '26px 34px',
            borderRadius: 18,
            backgroundColor: '#161B22',
            border: `2px solid ${COLORS.gold}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 15,
                color: COLORS.gold,
                fontWeight: 700,
              }}
            >
              TRIALSWARM RULE R1 DETERMINISTIC CONVERSION
            </div>
            <div
              style={{
                fontFamily: FONT_MONO,
                fontSize: 32,
                fontWeight: 800,
                marginTop: 8,
              }}
            >
              4.0 mg × (5.0 / 0.75) ={' '}
              <span style={{ color: COLORS.gold }}>
                26.67 mg/day Prednisone eq
              </span>
            </div>
          </div>
          <div
            style={{
              backgroundColor: COLORS.red,
              color: '#FFFFFF',
              padding: '14px 28px',
              borderRadius: 12,
              fontSize: 26,
              fontWeight: 800,
            }}
          >
            CONTRAINDICATED
          </div>
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 3B (Light, 424f): Live UI Verdict Capture (ui_01_pt102_hero.png)
const Scene3bPt102Ui: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, 424], [1.03, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const chipIn = interpolate(frame, [15, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="06 · Live Clinical Workstation Verdict"
        step="06 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '108px 72px 104px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div
          style={{
            opacity: chipIn,
            alignSelf: 'flex-start',
            backgroundColor: COLORS.darkBg,
            color: COLORS.darkInk,
            borderLeft: `5px solid ${COLORS.red}`,
            padding: '10px 22px',
            borderRadius: 10,
            fontFamily: FONT_MONO,
            fontSize: 20,
            fontWeight: 700,
          }}
        >
          Rule R1 Override: 26.67 mg/day Prednisone eq &gt; 10.0 mg ceiling →
          CONTRAINDICATED (32 ms)
        </div>

        <div
          style={{
            flex: 1,
            borderRadius: 18,
            overflow: 'hidden',
            border: `2px solid ${COLORS.terracotta}`,
            boxShadow: '0 14px 36px rgba(0,0,0,0.12)',
            backgroundColor: '#FFFFFF',
          }}
        >
          <Img
            src={staticFile('shots/ui_01_pt102_hero.png')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center 26%',
              transform: `scale(${zoom})`,
            }}
          />
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 4A (Dark, 390f): Antigravity /swarm Board Live Trace (ui_03_swarm_board.png)
const Scene4aSwarmBoard: React.FC = () => {
  const frame = useCurrentFrame();
  const messages = [
    {
      who: '@extractor',
      text: '10 criteria extracted with verbatim line citations',
      color: COLORS.blue,
      delay: 35,
    },
    {
      who: '@phenotyper',
      text: '14 clinical facts grounded to EHR lines',
      color: COLORS.purple,
      delay: 110,
    },
    {
      who: '@safety-auditor',
      text: 'R1 (26.67 mg Pred) + R2 (19d < 28d washout) FAIL',
      color: COLORS.gold,
      delay: 195,
    },
  ];

  return (
    <SceneIn dark>
      <SceneBadge
        label="07 · Antigravity /swarm Message Board"
        step="07 / 12"
        dark
      />
      <div
        style={{
          padding: '108px 72px 104px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          gap: 32,
          alignItems: 'stretch',
        }}
      >
        <div
          style={{
            flex: 0.72,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: 18,
          }}
        >
          <h2 style={{ fontSize: 44, fontWeight: 800, margin: 0 }}>
            Every Agent Logged in Real Time
          </h2>
          <p
            style={{
              fontSize: 21,
              color: COLORS.darkMuted,
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            The Antigravity /swarm board records every intermediate handoff so
            clinicians inspect the exact reasoning chain.
          </p>
          {messages.map((m) => {
            const p = interpolate(frame, [m.delay, m.delay + 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={m.who}
                style={{
                  opacity: p,
                  transform: `translateX(${(1 - p) * -20}px)`,
                  padding: '16px 20px',
                  borderRadius: 14,
                  backgroundColor: COLORS.darkCard,
                  border: `1.5px solid ${COLORS.darkBorder}`,
                  borderLeft: `5px solid ${m.color}`,
                }}
              >
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 18,
                    fontWeight: 800,
                    color: m.color,
                  }}
                >
                  {m.who}
                </div>
                <div style={{ fontSize: 19, marginTop: 6 }}>{m.text}</div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            flex: 1.28,
            borderRadius: 18,
            overflow: 'hidden',
            border: `2px solid ${COLORS.gold}`,
            backgroundColor: '#FFFFFF',
          }}
        >
          <Img
            src={staticFile('shots/ui_03_swarm_board.png')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center 28%',
            }}
          />
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 4B (Light, 413f): Rule R2 19d vs 28d Washout + Citation Click
const Scene4bWashoutAndCitation: React.FC = () => {
  const frame = useCurrentFrame();
  const barWidth = interpolate(frame, [40, 130], [0, (19 / 28) * 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="08 · Rule R2 Washout &amp; Line Grounding"
        step="08 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '108px 72px 104px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: 18,
        }}
      >
        <div
          style={{
            backgroundColor: COLORS.lightCard,
            border: `1.5px solid ${COLORS.lightBorder}`,
            borderRadius: 16,
            padding: '20px 28px',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
            }}
          >
            <span style={{ fontSize: 24, fontWeight: 800 }}>
              Rule R2: Anti-LAG-3 Checkpoint Washout Window
            </span>
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 20,
                fontWeight: 800,
                color: COLORS.red,
              }}
            >
              19 DAYS ELAPSED &lt; 28 DAYS REQUIRED (9 DAYS SHORT)
            </span>
          </div>
          <div
            style={{
              height: 28,
              borderRadius: 14,
              backgroundColor: '#E5E7EB',
              overflow: 'hidden',
              position: 'relative',
            }}
          >
            <div
              style={{
                width: `${barWidth}%`,
                height: '100%',
                backgroundColor: COLORS.red,
                borderRadius: 14,
              }}
            />
          </div>
        </div>

        <div
          style={{
            flex: 1,
            borderRadius: 18,
            overflow: 'hidden',
            border: `2px solid ${COLORS.green}`,
            boxShadow: '0 12px 32px rgba(0,0,0,0.10)',
            backgroundColor: '#FFFFFF',
          }}
        >
          <Img
            src={staticFile('shots/ui_02_citation_click.png')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center 35%',
            }}
          />
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 5 (Dark, 670f): Rule R6 Adversarial Hallucination Blocker
const Scene5AdversarialR6: React.FC = () => {
  const frame = useCurrentFrame();
  const gateScale = interpolate(frame, [160, 185], [0.95, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const gateOpacity = interpolate(frame, [160, 185], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneIn dark>
      <SceneBadge
        label="09 · Rule R6 Adversarial Probe (/judge)"
        step="09 / 12"
        dark
      />
      <div
        style={{
          padding: '108px 72px 104px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        <div
          style={{
            opacity: gateOpacity,
            transform: `scale(${gateScale})`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '16px 26px',
            borderRadius: 14,
            backgroundColor: COLORS.darkCard,
            border: `2px solid ${COLORS.greenSoft}`,
          }}
        >
          <div style={{ fontSize: 22, fontWeight: 700 }}>
            Injected Fake Quote:{' '}
            <span style={{ fontFamily: FONT_MONO, color: COLORS.redSoft }}>
              &quot;Patient is taking 0 mg corticosteroids&quot;
            </span>
          </div>
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 20,
              fontWeight: 800,
              color: '#0D1117',
              backgroundColor: COLORS.greenSoft,
              padding: '8px 18px',
              borderRadius: 10,
            }}
          >
            RULE R6: UNVERIFIED_CITATION_BLOCKED
          </div>
        </div>

        <div
          style={{
            flex: 1,
            borderRadius: 18,
            overflow: 'hidden',
            border: `2px solid ${COLORS.greenSoft}`,
            backgroundColor: '#FFFFFF',
          }}
        >
          <Img
            src={staticFile('shots/ui_05_judge_top.png')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center 18%',
            }}
          />
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 6 (Light, 730f): Cohort Scenarios PT-101, PT-103, PT-104
const Scene6CohortScenarios: React.FC = () => {
  const frame = useCurrentFrame();
  const cases = [
    {
      id: 'PT-101',
      name: 'Elena Rostova (62F, NSCLC)',
      detail: 'KRAS G12C+, PD-L1 65%, treated brain met > 14d, off steroids 30d',
      verdict: 'ELIGIBLE',
      color: COLORS.green,
      bg: '#ECFDF5',
      delay: 128,
    },
    {
      id: 'PT-103',
      name: 'Sofia Morales (57F, TNBC)',
      detail: '45 Gy thoracic RT 110d ago (< 180d) + AST 142 / ALT 156 Grade 2 LFTs',
      verdict: 'CONTRAINDICATED',
      color: COLORS.red,
      bg: '#FEF2F2',
      delay: 235,
    },
    {
      id: 'PT-104',
      name: 'David Chen (64M, Resected NSCLC)',
      detail: 'KRAS G12C+ ctDNA, PD-L1 & EGFR/ALK tissue panel pending',
      verdict: 'NEEDS HUMAN REVIEW',
      color: '#D97706',
      bg: '#FFFBEB',
      delay: 435,
    },
  ];

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="10 · Multi-Archetype Oncology Routing"
        step="10 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '122px 72px 110px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <h2 style={{ fontSize: 54, fontWeight: 800, margin: 0 }}>
            Safe Routing Across Diverse Oncology Profiles
          </h2>
          <p
            style={{
              fontSize: 24,
              color: COLORS.lightMuted,
              marginTop: 10,
              marginBottom: 0,
            }}
          >
            Zero silent assumptions when lab grades cross thresholds or
            biomarkers are pending.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 28 }}>
          {cases.map((c) => {
            const p = interpolate(frame, [c.delay, c.delay + 24], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing: Easing.out(Easing.cubic),
            });
            return (
              <div
                key={c.id}
                style={{
                  flex: 1,
                  opacity: p,
                  transform: `translateY(${(1 - p) * 24}px)`,
                  backgroundColor: COLORS.lightCard,
                  border: `2px solid ${c.color}`,
                  borderRadius: 20,
                  padding: 30,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minHeight: 360,
                  boxShadow: '0 10px 26px rgba(0,0,0,0.06)',
                }}
              >
                <div>
                  <div
                    style={{
                      fontFamily: FONT_MONO,
                      fontSize: 18,
                      fontWeight: 800,
                      color: c.color,
                    }}
                  >
                    {c.id}
                  </div>
                  <div
                    style={{
                      fontSize: 28,
                      fontWeight: 800,
                      marginTop: 10,
                      lineHeight: 1.2,
                    }}
                  >
                    {c.name}
                  </div>
                  <div
                    style={{
                      fontSize: 21,
                      color: COLORS.lightMuted,
                      marginTop: 16,
                      lineHeight: 1.45,
                    }}
                  >
                    {c.detail}
                  </div>
                </div>

                <div
                  style={{
                    marginTop: 24,
                    padding: '14px 18px',
                    borderRadius: 12,
                    backgroundColor: c.bg,
                    border: `1.5px solid ${c.color}`,
                    color: c.color,
                    fontFamily: FONT_MONO,
                    fontSize: 20,
                    fontWeight: 800,
                    textAlign: 'center',
                  }}
                >
                  {c.verdict}
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            fontFamily: FONT_MONO,
            fontSize: 18,
            color: COLORS.lightMuted,
            textAlign: 'center',
          }}
        >
          Every verdict includes verbatim EHR line anchors + protocol rule IDs
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 7A (Dark, 360f): 120-Case Benchmark Scorecard
const Scene7aBenchmark: React.FC = () => {
  const frame = useCurrentFrame();
  const tsBar = interpolate(frame, [15, 75], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const llmBar = interpolate(frame, [25, 85], [0, 47.5], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  return (
    <SceneIn dark>
      <SceneBadge
        label="11 · Verified Cohort Benchmark (n = 120)"
        step="11 / 12"
        dark
      />
      <div
        style={{
          padding: '126px 72px 110px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
        }}
      >
        <h2 style={{ fontSize: 64, fontWeight: 800, margin: 0 }}>
          100.0% Exact Accuracy{' '}
          <span style={{ color: COLORS.greenSoft }}>(120 / 120)</span>
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 28,
                fontWeight: 800,
                marginBottom: 10,
              }}
            >
              <span>TrialSwarm AI (/swarm + Rules R1–R6)</span>
              <span style={{ fontFamily: FONT_MONO, color: COLORS.greenSoft }}>
                100.0% (0 mismatches)
              </span>
            </div>
            <div
              style={{
                height: 44,
                borderRadius: 12,
                backgroundColor: '#21262D',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${tsBar}%`,
                  height: '100%',
                  backgroundColor: COLORS.green,
                  borderRadius: 12,
                }}
              />
            </div>
          </div>

          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: 28,
                fontWeight: 700,
                color: COLORS.darkMuted,
                marginBottom: 10,
              }}
            >
              <span>Naive Single-Prompt LLM Baseline</span>
              <span style={{ fontFamily: FONT_MONO, color: COLORS.redSoft }}>
                47.5% (30.0% specificity)
              </span>
            </div>
            <div
              style={{
                height: 44,
                borderRadius: 12,
                backgroundColor: '#21262D',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${llmBar}%`,
                  height: '100%',
                  backgroundColor: COLORS.red,
                  borderRadius: 12,
                }}
              />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 22 }}>
          {[
            ['R1 Steroid', '15 / 15'],
            ['R2–R3 Washout & RT', '30 / 30'],
            ['R4 CTCAE Organ', '15 / 15'],
            ['R5 Reflex Biomarker', '30 / 30'],
          ].map(([label, score]) => (
            <div
              key={label}
              style={{
                flex: 1,
                backgroundColor: COLORS.darkCard,
                border: `1.5px solid ${COLORS.darkBorder}`,
                borderRadius: 16,
                padding: '22px 24px',
              }}
            >
              <div style={{ fontSize: 19, color: COLORS.darkMuted }}>
                {label}
              </div>
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 800,
                  color: COLORS.greenSoft,
                  marginTop: 8,
                }}
              >
                {score}
              </div>
            </div>
          ))}
        </div>
      </div>
    </SceneIn>
  );
};

// Scene 7B (Light, 349f): SHA-256 Digital Sign-Off & Closing
const Scene7bSignoffClose: React.FC = () => {
  const frame = useCurrentFrame();
  const badgeIn = interpolate(frame, [20, 45], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneIn dark={false} fromDark>
      <SceneBadge
        label="12 · SHA-256 Sign-Off · FDA Inspection Ready"
        step="12 / 12"
        dark={false}
      />
      <div
        style={{
          padding: '108px 72px 104px',
          height: '100%',
          boxSizing: 'border-box',
          display: 'flex',
          gap: 32,
          alignItems: 'stretch',
        }}
      >
        <div
          style={{
            flex: 1.25,
            borderRadius: 18,
            overflow: 'hidden',
            border: `2px solid ${COLORS.green}`,
            boxShadow: '0 14px 36px rgba(0,0,0,0.12)',
            backgroundColor: '#FFFFFF',
          }}
        >
          <Img
            src={staticFile('shots/ui_04_signoff_modal.png')}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              objectPosition: 'center 92%',
            }}
          />
        </div>

        <div
          style={{
            flex: 0.75,
            opacity: badgeIn,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            gap: 18,
          }}
        >
          <div
            style={{
              fontFamily: FONT_MONO,
              fontSize: 16,
              fontWeight: 800,
              color: COLORS.terracotta,
            }}
          >
            TAMPER-EVIDENT AUDIT TRAIL
          </div>
          <h2 style={{ fontSize: 46, fontWeight: 800, margin: 0, lineHeight: 1.1 }}>
            TrialSwarm AI
          </h2>
          <p
            style={{
              fontSize: 22,
              color: COLORS.lightMuted,
              margin: 0,
              lineHeight: 1.45,
            }}
          >
            Built with Antigravity <span style={{ fontFamily: FONT_MONO }}>/swarm</span>{' '}
            + deterministic clinical rules R1–R6.
          </p>
          <div
            style={{
              padding: '18px 22px',
              borderRadius: 14,
              backgroundColor: COLORS.lightCard,
              border: `1.5px solid ${COLORS.lightBorder}`,
              fontFamily: FONT_MONO,
              fontSize: 17,
              lineHeight: 1.6,
            }}
          >
            <div>✓ 120 / 120 exact cohort match</div>
            <div>✓ 0 unverified citations (R6)</div>
            <div>✓ SHA-256 coordinator sign-off</div>
            <div>✓ Live public demo on Modal</div>
          </div>
        </div>
      </div>
    </SceneIn>
  );
};

export const TrialSwarmDemo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.darkBg }}>
      {/* Continuous Voiceover Audio Tracks (zero overlap, 8f gap between tracks, +3.2 dB gain) */}
      <Sequence from={S1_START} durationInFrames={S1_DUR}>
        <Audio src={staticFile('audio/demo_01_problem.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S2_START} durationInFrames={S2_DUR}>
        <Audio src={staticFile('audio/demo_02_architecture.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S3_START} durationInFrames={S3_DUR}>
        <Audio src={staticFile('audio/demo_03_pt102_walkthrough.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S4_START} durationInFrames={S4_DUR}>
        <Audio src={staticFile('audio/demo_04_swarm_board.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S5_START} durationInFrames={S5_DUR}>
        <Audio src={staticFile('audio/demo_05_r6_adversarial_trap.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S6_START} durationInFrames={S6_DUR}>
        <Audio src={staticFile('audio/demo_06_cohort_scenarios.mp3')} volume={1.45} />
      </Sequence>
      <Sequence from={S7_START} durationInFrames={S7_DUR}>
        <Audio src={staticFile('audio/demo_07_benchmark_signoff.mp3')} volume={1.45} />
      </Sequence>

      {/* Strictly Sequential Non-Overlapping Visual Scenes */}
      <Sequence from={S1_START} durationInFrames={DEMO_SCENES.s1a}>
        <Scene1aProblemHook />
      </Sequence>
      <Sequence
        from={S1_START + DEMO_SCENES.s1a}
        durationInFrames={DEMO_SCENES.s1b}
      >
        <Scene1bTrapsDetail />
      </Sequence>
      <Sequence from={S2_START} durationInFrames={DEMO_SCENES.s2a}>
        <Scene2aSwarmFlow />
      </Sequence>
      <Sequence
        from={S2_START + DEMO_SCENES.s2a}
        durationInFrames={DEMO_SCENES.s2b}
      >
        <Scene2bRulesCascade />
      </Sequence>
      <Sequence from={S3_START} durationInFrames={DEMO_SCENES.s3a}>
        <Scene3aPt102Trap />
      </Sequence>
      <Sequence
        from={S3_START + DEMO_SCENES.s3a}
        durationInFrames={DEMO_SCENES.s3b}
      >
        <Scene3bPt102Ui />
      </Sequence>
      <Sequence from={S4_START} durationInFrames={DEMO_SCENES.s4a}>
        <Scene4aSwarmBoard />
      </Sequence>
      <Sequence
        from={S4_START + DEMO_SCENES.s4a}
        durationInFrames={DEMO_SCENES.s4b}
      >
        <Scene4bWashoutAndCitation />
      </Sequence>
      <Sequence from={S5_START} durationInFrames={DEMO_SCENES.s5}>
        <Scene5AdversarialR6 />
      </Sequence>
      <Sequence from={S6_START} durationInFrames={DEMO_SCENES.s6}>
        <Scene6CohortScenarios />
      </Sequence>
      <Sequence from={S7_START} durationInFrames={DEMO_SCENES.s7a}>
        <Scene7aBenchmark />
      </Sequence>
      <Sequence
        from={S7_START + DEMO_SCENES.s7a}
        durationInFrames={DEMO_SCENES.s7b}
      >
        <Scene7bSignoffClose />
      </Sequence>

      <RootCaptions />
      <RootProgressBar />
    </AbsoluteFill>
  );
};
