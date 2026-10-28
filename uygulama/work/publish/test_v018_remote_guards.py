"""Small pure guards for v0.18's partial annotated-tag snapshot handling."""
import copy
import unittest
from verify_remote_v018 import prior_tag_pairs, raw_refs, release_map


def fixture():
    old, latest, commit = '1' * 40, '2' * 40, '3' * 40
    refs = [
        {'ref': 'refs/tags/v0.16.0', 'object': {'type': 'tag', 'sha': old}},
        {'ref': 'refs/tags/v0.17.0', 'object': {'type': 'tag', 'sha': latest}},
    ]
    pairs = {'refs/tags/v0.16.0': old, 'refs/tags/v0.16.0^{}': '4' * 40}
    objects = {latest: {'sha': latest, 'tag': 'v0.17.0', 'object': {'type': 'commit', 'sha': commit}}}
    return refs, pairs, objects, commit


class PriorTagGuards(unittest.TestCase):
    def test_latest_only_object_preserves_old_peeled_commit(self):
        refs, pairs, objects, head = fixture()
        result = prior_tag_pairs(refs, pairs, objects, latest_head=head)
        self.assertEqual(result['refs/tags/v0.16.0^{}'], '4' * 40)
        self.assertEqual(result['refs/tags/v0.17.0^{}'], head)
        self.assertEqual(len(result), 4)
        self.assertEqual(len(pairs), 2)

    def test_changed_old_raw_ref_rejected(self):
        refs, pairs, objects, head = fixture()
        refs[0]['object']['sha'] = '5' * 40
        with self.assertRaises(AssertionError):
            prior_tag_pairs(refs, pairs, objects, latest_head=head)

    def test_missing_old_peeled_ref_rejected(self):
        refs, pairs, objects, head = fixture()
        pairs.pop('refs/tags/v0.16.0^{}')
        with self.assertRaises(AssertionError):
            prior_tag_pairs(refs, pairs, objects, latest_head=head)

    def test_missing_old_raw_ref_rejected(self):
        refs, pairs, objects, head = fixture()
        pairs.pop('refs/tags/v0.16.0')
        with self.assertRaises(AssertionError):
            prior_tag_pairs(refs, pairs, objects, latest_head=head)

    def test_wrong_latest_peeled_head_rejected(self):
        refs, pairs, objects, _ = fixture()
        with self.assertRaises(AssertionError):
            prior_tag_pairs(refs, pairs, objects, latest_head='6' * 40)

    def test_wrong_latest_object_tag_rejected(self):
        refs, pairs, objects, head = fixture()
        objects[refs[1]['object']['sha']]['tag'] = 'v0.18.0'
        with self.assertRaises(AssertionError):
            prior_tag_pairs(refs, pairs, objects, latest_head=head)

    def test_duplicate_raw_ref_rejected(self):
        refs, *_ = fixture()
        refs.append(copy.deepcopy(refs[0]))
        with self.assertRaises(AssertionError):
            raw_refs(refs)

    def test_lightweight_tag_rejected(self):
        refs, *_ = fixture()
        refs[0]['object']['type'] = 'commit'
        with self.assertRaises(AssertionError):
            raw_refs(refs)


class AssetHistoryGuards(unittest.TestCase):
    @staticmethod
    def release():
        return {'tag_name': 'v0.17.0', 'id': 10, 'assets': [
            {'id': 21, 'name': 'b', 'size': 2, 'digest': 'sha256:bbb'},
            {'id': 20, 'name': 'a', 'size': 1, 'digest': None}]}

    def test_asset_order_and_count_are_observed_not_hardcoded(self):
        release = self.release()
        result = release_map([release])
        self.assertEqual([a['name'] for a in result['v0.17.0']['assets']], ['a', 'b'])
        release['assets'].append({'id': 22, 'name': 'c', 'size': 3, 'digest': 'sha256:ccc'})
        self.assertEqual(len(release_map([release])['v0.17.0']['assets']), 3)

    def test_duplicate_release_tag_rejected(self):
        release = self.release()
        duplicate = copy.deepcopy(release)
        duplicate['id'] = 11
        duplicate['assets'] = []
        with self.assertRaises(AssertionError):
            release_map([release, duplicate])

    def test_duplicate_asset_name_rejected(self):
        release = self.release()
        release['assets'][1]['name'] = 'b'
        with self.assertRaises(AssertionError):
            release_map([release])

    def test_duplicate_asset_id_across_releases_rejected(self):
        first = self.release()
        second = {'tag_name': 'v0.16.0', 'id': 11, 'assets': [
            {'id': 21, 'name': 'different-name', 'size': 0}]}
        with self.assertRaises(AssertionError):
            release_map([first, second])


if __name__ == '__main__':
    unittest.main()
