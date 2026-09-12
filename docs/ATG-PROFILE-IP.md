# ATG:IP

Status: CANONICAL DOMAIN PROFILE v1

`ATG:IP` is the Atralith domain profile for intellectual-property identity, authority, licensing, filing, portfolio lifecycle, and downstream authorization.

It extends ATG CORE. It does not fork or replace ATG.

## Core vocabulary

- `IP:REGISTER`
- `IP:VERIFY`
- `IP:OWNER`
- `IP:CANON`
- `IP:GRANT`
- `IP:LICENSE`
- `IP:ADAPT`
- `IP:DERIVE`
- `IP:REMIX`
- `IP:COMMERCIALIZE`
- `IP:ASSIGN`
- `IP:POOL`
- `IP:REVOKE`
- `IP:EXPIRE`
- `IP:RENEW`
- `IP:WATCH`
- `IP:FILE`
- `IP:STATUS`
- `IP:RECEIPT`

## Authority rule

ATG:IP expresses authority. It does not create authority merely by emitting a token.

Every consequential IP action resolves through:

`Identity -> Mandate -> IP Authority -> Policy -> Professional/Human Gate when required -> Tool Permission -> Execution -> Receipt -> Audit`

## Consumer examples

### ARCANA54

```text
IP:VERIFY {
  work: STORY:001
  action: POCKET:COMPILE
  use: COMMERCIAL
  territory: GLOBAL
}
```

ARCANA54 proceeds only when the requested transformation is within scope.

### Holofoil

```text
IP:VERIFY {
  work: STORY:001
  action: HOLO:MANIFEST
  use: COLLECTIBLE
}
```

Holofoil consumes the authority receipt and displays the resulting rights summary. It does not silently create holder rights.

### CHOAS GAMING PRODUCTIONS (GDP)

```text
IP:VERIFY {
  work: WORLD:001
  action: PLAY:PRODUCE
  rights: [GAME_ADAPTATION, CHARACTER_USE, COMMERCIAL_DISTRIBUTION]
}
```

## Filing intents

```text
IP:FILE { office: USPTO, type: TRADEMARK }
IP:FILE { office: USPTO, type: PATENT }
IP:FILE { office: USCO, type: COPYRIGHT }
IP:FILE { office: WIPO, route: MADRID }
IP:FILE { office: WIPO, route: HAGUE }
IP:FILE { office: WIPO, route: PCT }
```

National/regional adapters remain jurisdiction-specific.

## NTRU / NTRUtv boundary

NTRU is Neteru lore for `neteru.xyz` and is not an ATG:IP trust/provenance subsystem.

NTRUtv is a separate media/application surface. It may receive authorized media like other distribution/exhibition surfaces, but it does not grant IP authority.
