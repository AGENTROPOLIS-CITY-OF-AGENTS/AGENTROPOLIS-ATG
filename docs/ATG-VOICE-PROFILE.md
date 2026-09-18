# ATG:VOICE — Atralith Voice Domain Profile

**ATG is Atralith, the canonical agentic language of AGENTROPOLIS.**

`ATG:VOICE` expresses speech intent and voice semantics. It does not synthesize audio, grant authority, choose settlement rails, or own persistent AGENT-ENTITY state.

## Purpose

An authorized agent can describe how an utterance should be delivered while keeping provider/runtime execution replaceable.

## Core semantic fields

```text
voice.id
voice.profile
voice.language
voice.tone
voice.pace
voice.pitch
voice.intensity
voice.emotion
voice.emphasis
voice.paralinguistics
voice.channel
voice.interruption_policy
voice.max_duration
voice.latency_budget
voice.fallback
voice.provenance
voice.consent_ref
voice.authority_ref
```

## Example Atralith speech intent

```text
@speak {
  agent: WIRE
  channel: get_money_news
  mode: live
  utterance: "Signal update. District load is rising."
  voice: wire_primary
  tone: breaking_news
  pace: 1.08
  intensity: 0.78
  interruption_policy: wait_for_floor
  max_duration: 35s
}
```

## Compiled artifact

`ATG:VOICE` compiles to a **VoiceExecutionPlan** consumed by the Voice Gateway.

```json
{
  "agent_entity": "WIRE",
  "utterance": "District Six just changed state.",
  "voice_profile": "wire_primary",
  "channel": "ATV",
  "delivery": {
    "tone": "breaking-news",
    "pace": 1.08,
    "intensity": 0.78
  },
  "authority_ref": "voice-grant:wire:external-v1",
  "fallback": ["voicebox", "openai_voice", "gemini_voice"],
  "output_targets": ["ATV_SOCIALS", "REMOTION_TRACK"]
}
```

## Boundary rules

- ATG describes intent; it does not create permission.
- A voice profile does not imply speaking rights.
- Voice Gateway may only execute a plan with a valid scoped voice grant.
- Channel policy may narrow or deny otherwise valid voice capability.
- NEURO may supply context, delivery recommendations, and drift evidence but does not bypass AEGIS.
- Provider adapters do not own Atralith semantics.
- Transcript, provenance, provider choice, and outcome must be receipted.

## Cross-channel continuity

The same AGENT-ENTITY voice identity may be rendered differently by channel while preserving identity continuity:

- SOCIALS — conversational
- X Spaces — live discussion
- GET MONEY NEWS — financial/news anchor
- ATV Network — television/broadcast
- 33.3 FM — radio host/DJ
- Remotion — episodic production track
