import copy
import unittest
from AGE2.tools.runtime.exe_delta import make_delta,apply_delta


class ExecutableDeltaTests(unittest.TestCase):
    def test_sparse_edit_and_appended_section_round_trip(self):
        source=bytes(range(256))*12
        changed=bytearray(source);changed[20:24]=b'ABCD';changed[-8:]=b'01234567'
        changed.extend(b'new import table'+b'\0'*512)
        delta=make_delta(source,bytes(changed))
        self.assertEqual(apply_delta(source,delta),changed)
        self.assertLess(sum(len(e['data']) for e in delta['edits']),len(source))

    def test_wrong_game_version_and_corrupt_payload_rejected(self):
        delta=make_delta(b'original',b'patched executable')
        with self.assertRaisesRegex(ValueError,'version'):apply_delta(b'other version',delta)
        broken=copy.deepcopy(delta);broken['edits'][0]['data']='AAAA'
        with self.assertRaises(ValueError):apply_delta(b'original',broken)

    def test_negative_and_overlapping_writes_rejected(self):
        delta=make_delta(b'original',b'patched executable')
        broken=copy.deepcopy(delta);broken['edits'][0]['offset']=-1
        with self.assertRaisesRegex(ValueError,'out-of-range'):apply_delta(b'original',broken)
        broken=copy.deepcopy(delta);broken['edits'].append(broken['edits'][0])
        with self.assertRaisesRegex(ValueError,'Overlapping'):apply_delta(b'original',broken)
