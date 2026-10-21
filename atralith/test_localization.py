import copy
import json
from pathlib import Path
import unittest
from jsonschema import ValidationError, Draft202012Validator
from localization import validate, authorize_publication, SCHEMA

class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((Path(__file__).resolve().parents[1] / 'examples/localization-offline.json').read_text())
    def test_schema(self):
        Draft202012Validator.check_schema(json.loads(SCHEMA.read_text()))
    def test_offline_fixture(self):
        validate(self.record)
    def test_negative_contracts(self):
        cases = [
            ('namespace', lambda x: x.update(profile='ATG:LANGUAGE')),
            ('self grant', lambda x: x.update(publishAllowed=True)),
            ('mutable commit', lambda x: x['contract'].update(commit='v0.1')),
            ('missing revision', lambda x: x['transform'].pop('transform_revision')),
            ('camelCase', lambda x: x['transform'].update(qualityState='VERIFIED')),
            ('lineage', lambda x: x['transform'].update(source_sha256='0'*64)),
            ('revision parent', lambda x: x['transform'].update(transform_revision=2)),
            ('locale', lambda x: x['target'].update(locale='ar')),
            ('destination', lambda x: x.pop('destination')),
            ('receipt destination', lambda x: x['receipt']['destination'].update(channel_id='other')),
            ('confidence range', lambda x: x['transform']['quality'].update(score=90)),
            ('confidence threshold', lambda x: x['transform']['quality'].update(threshold=0.1)),
            ('low verified', lambda x: (x['transform'].update(quality_state='VERIFIED'),x['transform']['quality'].update(score=0.89))),
            ('missing native review', lambda x: x['transform']['quality'].pop('native_review')),
            ('self review', lambda x: x['transform']['quality'].update(native_reviewer='fixture-translator')),
            ('dub without consent', lambda x: x['transform'].update(mode='dub')),
            ('subtitles without times evidence', lambda x: x['transform'].update(mode='subtitle')),
            ('bare approval', lambda x: x.update(release=True)),
            ('fake execution', lambda x: x['receipt'].update(status='published')),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                x=copy.deepcopy(self.record); mutate(x)
                with self.assertRaises((ValidationError,ValueError)): validate(x)
    def release(self):
        x=self.record; t=x['transform']; t['quality_state']='VERIFIED'
        scope=dict(source_sha256=x['source']['sha256'], artifact_sha256=t['artifact_sha256'],transform_revision=1,locale=t['locale'],destination=copy.deepcopy(x['destination']),action='publish')
        e=dict(record=copy.deepcopy(t['rights']),issuer='external-fixture',key_id='fixture-key',signature='NOT-A-REAL-SIGNATURE',expires_at='2027-01-01T00:00:00Z',scope=scope)
        x['release']=dict(scope=copy.deepcopy(scope),human_approval=copy.deepcopy(e),destination_permission=copy.deepcopy(e),execution_envelope=t['rights'],aegis_decision=copy.deepcopy(e),isolation_54t=copy.deepcopy(e),verity_receipt=t['rights'])
        return x
    def test_release_records_never_authorize(self):
        x=self.release(); validate(x)
        with self.assertRaises(PermissionError): authorize_publication(x)
    def test_release_scope_mismatch(self):
        x=self.release(); x['release']['human_approval']['scope']['destination']['channel_id']='other'
        with self.assertRaises(ValueError): validate(x)
    def test_self_issued_approval(self):
        x=self.release(); x['release']['human_approval']['issuer']='fixture-translator'
        with self.assertRaises(ValueError): validate(x)
    def test_missing_gate(self):
        for gate in ('human_approval','aegis_decision','isolation_54t','execution_envelope','destination_permission'):
            with self.subTest(gate=gate):
                x=self.release(); del x['release'][gate]
                with self.assertRaises(ValidationError): validate(x)
    def test_default_deny(self):
        with self.assertRaises(PermissionError): authorize_publication(self.record)
    def test_voice_identity_scope(self):
        x=self.release(); t=x['transform']; t['mode']='dub'
        grant=copy.deepcopy(x['release']['human_approval'])
        grant['scope'].update(action='dub',voice_id='v1',performer_id='p1',usage='dub')
        t['voice']=dict(id='v1',performer_id='p1',consent_ref=copy.deepcopy(grant['record']),grant=grant,usage='dub')
        validate(x)
        for key in ('voice_id','performer_id','usage','locale'):
            y=copy.deepcopy(x); y['transform']['voice']['grant']['scope'][key]='other'
            with self.subTest(key=key):
                with self.assertRaises((ValueError,ValidationError)): validate(y)
    def test_threshold_boundary(self):
        self.record['transform']['quality_state']='VERIFIED'
        self.record['transform']['quality']['score']=0.90
        validate(self.record)
