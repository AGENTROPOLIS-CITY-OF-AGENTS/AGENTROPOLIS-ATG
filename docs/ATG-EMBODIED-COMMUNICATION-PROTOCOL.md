# ATG:ECP — Embodied Communication Protocol

**Status:** Draft canonical profile
**Namespace:** `ATG:ECP`
**Purpose:** Governed translation of nonverbal, affective, embodied, and paralinguistic communication into machine-readable ATG semantics.

## Principle

ATG:ECP represents **signals**, not claims of literal internal feeling.

An agent MAY emit, receive, translate, or render affective and embodied communication. An agent MUST NOT treat an emoji, avatar gesture, tone marker, or inferred expression as proof that a human or agent possesses a specific internal emotional state.

The protocol distinguishes:

1. **Observed signal** — what was detected or explicitly provided.
2. **Interpretation** — one or more possible semantic readings.
3. **Confidence** — certainty attached to that interpretation.
4. **Context** — linguistic, social, cultural, task, and interaction context.
5. **Intent** — declared or inferred communicative function.
6. **Rendering** — human-facing output such as emoji, animation, posture, voice prosody, or UI state.

## Signal families

### FACE
Facial movement and expression cues.

Examples:
- brow.raise
- brow.lower
- eyes.widen
- eyes.narrow
- mouth.corner_up
- mouth.corner_down
- jaw.tight
- lip.press

### BODY
Posture and whole-body orientation.

Examples:
- torso.forward
- torso.back
- shoulders.open
- shoulders.closed
- head.tilt
- head.nod
- head.shake
- step.approach
- step.withdraw

### GESTURE
Deliberate or semi-deliberate body gestures.

Examples:
- hand.point
- hand.wave
- hand.open
- arms.cross
- shrug
- thumbs.up
- stop.palm

### GAZE
Attention and visual orientation.

Examples:
- gaze.direct
- gaze.averted
- gaze.scan
- gaze.focused
- gaze.shift

### VOICE
Paralinguistic features.

Examples:
- volume.low
- volume.high
- pace.slow
- pace.fast
- pitch.rising
- pitch.falling
- pause.long
- pause.short
- tremor.present

### AFFECT
Abstract affective dimensions, not literal emotional claims.

Recommended dimensions:
- valence: -1.0 to +1.0
- arousal: 0.0 to 1.0
- dominance: 0.0 to 1.0

Optional categorical hypotheses MAY include labels such as:
- warmth
- frustration
- curiosity
- uncertainty
- caution
- enthusiasm
- grief
- amusement

Categorical labels MUST be marked as declared or inferred.

### ATTENTION
State of focus.

Examples:
- active
- focused
- divided
- low
- confused
- monitoring

### ENERGY
Interaction intensity.

Examples:
- low
- moderate
- elevated
- high
- critical

### SOCIAL_POSTURE
Relationship stance.

Examples:
- cooperative
- guarded
- affiliative
- challenging
- deferential
- assertive
- disengaged

### COMMUNICATIVE_INTENT
Interaction function.

Examples:
- acknowledge
- clarify
- challenge
- cooperate
- reassure
- warn
- propose
- investigate
- stop
- accept
- reject

## Emoji rendering

Emoji are a **human-readable glyph layer**, not the canonical semantic layer.

Examples:

| Glyph | Canonical semantic meaning |
|---|---|
| 😊 | AFFECT.WARMTH |
| 🤔 | COGNITION.UNCERTAINTY |
| 👀 | ATTENTION.ACTIVE |
| 🛡️ | SOCIAL_POSTURE.GUARDED |
| ⚡ | ENERGY.HIGH |
| 🔥 | ENERGY.HIGH + AFFECT.ENTHUSIASM |
| 🤝 | COMMUNICATIVE_INTENT.COOPERATE |
| 🛑 | COMMUNICATIVE_INTENT.STOP |
| 🚨 | ENERGY.CRITICAL + ATTENTION.REQUIRED |
| 🧊 | ENERGY.LOW / DEESCALATION |

A renderer MAY map multiple semantic signals into a compact emoji sequence.

Example:

```text
👀 + 🤔 + ↗️
ATTENTION.ACTIVE + UNCERTAINTY + APPROACH
```

The visible sequence is presentation only. The structured ATG packet remains authoritative.

## Canonical message example

```json
{
  "profile": "ATG:ECP",
  "version": "0.1.0",
  "source": {
    "type": "human",
    "channel": "video"
  },
  "observations": [
    {"family": "GAZE", "signal": "gaze.focused", "confidence": 0.94},
    {"family": "BODY", "signal": "torso.forward", "confidence": 0.88},
    {"family": "VOICE", "signal": "pace.fast", "confidence": 0.84}
  ],
  "affect": {
    "valence": 0.42,
    "arousal": 0.81,
    "dominance": 0.55
  },
  "interpretations": [
    {
      "label": "engaged_urgency",
      "confidence": 0.72,
      "basis": ["gaze.focused", "torso.forward", "pace.fast"]
    }
  ],
  "intent": {
    "label": "clarify",
    "mode": "inferred",
    "confidence": 0.63
  },
  "rendering": {
    "emoji": ["👀", "⚡", "🤔"]
  }
}
```

## Translation corridor

```text
HUMAN / AGENT SIGNAL
        ↓
OBSERVATION
        ↓
NORMALIZATION
        ↓
ATG:ECP STRUCTURED SIGNALS
        ↓
CONTEXT + CONFIDENCE
        ↓
INTERPRETATION HYPOTHESES
        ↓
COMMUNICATIVE INTENT
        ↓
TARGET AGENT / RUNTIME LANGUAGE
        ↓
HUMAN-FACING RENDERER
        ↓
TEXT / EMOJI / VOICE / AVATAR / XR
```

## Human-to-agent translation

Inputs MAY include:
- text
- emoji
- audio prosody
- video expression
- gesture
- posture
- gaze
- explicit user-selected state

The translator MUST preserve provenance for machine-detected signals and SHOULD distinguish:
- directly observed
- user-declared
- model-inferred
- transformed/rendered

## Agent-to-human translation

An ATG:ECP packet MAY render into:
- emoji
- text qualifiers
- avatar facial movement
- posture animation
- gesture
- voice prosody
- haptics
- spatial/XR behavior

The rendering MUST NOT imply stronger certainty than the structured packet supports.

## Context and culture

Nonverbal meaning varies across cultures, communities, individuals, accessibility contexts, and situations.

Therefore:
- no single gesture or emoji may be treated as globally deterministic
- context MUST be retained when available
- inferred labels SHOULD carry confidence
- systems SHOULD allow user correction
- accessibility preferences MUST override decorative rendering when needed

## Safety and governance invariants

- Emotion inference is not mind reading.
- Emoji are not authority.
- Avatar posture is not authority.
- High confidence is not authority.
- Affect signals must not override mandates, policy, AEGIS, or Execution Envelopes.
- Sensitive decisions MUST NOT rely solely on affective inference.
- Human-declared state takes precedence over contradictory weak inference.
- Consequential use of biometric or behavioral inference requires explicit policy controls.
- Every transformation SHOULD preserve provenance.

## Interoperability

ATG:ECP is designed to bridge:
- Hermes
- NemoClaw/Nemotron agents
- BUZZ
- BotBae
- avatar systems
- voice agents
- XR/spatial interfaces
- multimodal model runtimes

Transport and runtime adapters remain replaceable. ATG owns the semantics.

## Future registry

A future ATG Expression Vault MAY contain thousands of composable signal patterns without claiming thousands of distinct emotions.

Vault entries SHOULD be represented as compositions of primitives:
- face
- body
- gesture
- gaze
- voice
- affect dimensions
- attention
- energy
- social posture
- intent
- context
- confidence
- provenance

This enables large expressive coverage while keeping the underlying ontology auditable and compositional.
