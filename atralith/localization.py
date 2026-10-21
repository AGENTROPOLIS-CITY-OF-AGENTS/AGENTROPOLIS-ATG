"""Offline checks. No signer, network adapter, dispatcher or publication capability."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
SCHEMA = Path(__file__).resolve().parents[1] / 'contracts/localization-v0.1.schema.json'
def validate(record):
    Draft202012Validator(json.loads(SCHEMA.read_text()), format_checker=FormatChecker()).validate(record)
    t, source, target = record['transform'], record['source'], record['target']
    def require(value, message):
        if not value: raise ValueError(message)
    require(t['source_sha256'] == source['sha256'] and t['source_commit'] == source['commit'], 'source lineage mismatch')
    require(t['locale'] == target['locale'], 'locale mismatch')
    require((t['transform_revision'] == 1) == (t['previous_transform'] is None), 'revision lineage required')
    # Conservative pilot allowlist; not a general BCP-47 parser. Arabic remains unresolved.
    require(source['locale'] in {'en-US','es-419','pt-BR','fr-FR','ja-JP'}, 'unsupported source locale')
    require(target['locale'] in {'es-419','pt-BR','fr-FR','ja-JP'}, 'unsupported/unresolved target locale')
    require(t['quality']['native_reviewer'] != t['quality']['producer'], 'independent native reviewer required')
    if t['quality_state'] == 'VERIFIED':
        require(t['quality']['score'] >= t['quality']['threshold'], 'low confidence')
    expected = dict(source_sha256=source['sha256'], artifact_sha256=t['artifact_sha256'], transform_revision=t['transform_revision'], locale=t['locale'], destination=record['destination'], action='publish')
    receipt = record['receipt']
    for key in ('source_sha256','artifact_sha256','transform_revision','destination'):
        require(receipt[key] == expected[key], 'receipt binding mismatch: ' + key)
    require(receipt['contract_commit'] == record['contract']['commit'], 'receipt contract mismatch')
    release = record['release']
    if release is not None:
        require(t['quality_state'] == 'VERIFIED', 'unverified release')
        require(release['scope'] == expected, 'release scope mismatch')
        for key in ('human_approval','destination_permission','aegis_decision','isolation_54t'):
            require(release[key]['scope'] == expected, 'evidence scope mismatch: ' + key)
            require(release[key]['issuer'] != t['quality']['producer'], 'self-issued authority')
    if t['mode'] == 'dub':
        dub_scope = dict(expected, action='dub', voice_id=t['voice']['id'], performer_id=t['voice']['performer_id'], usage='dub')
        require(t['voice']['grant']['scope'] == dub_scope, 'voice scope mismatch')
        require(t['voice']['grant']['record'] == t['voice']['consent_ref'], 'voice consent reference mismatch')
    return record

def authorize_publication(record):
    validate(record)
    raise PermissionError('Publication disabled: external trusted human/54T/AEGIS/envelope verification is not implemented')
