"""Small analytic counterexamples; no compiler, solver or download is invoked."""
from pathlib import Path
import io
import json
import tempfile
import tarfile
import unittest
import zipfile

from build_su2 import (OPTIONS, PIN, CAP_FILE, archive_files, commands, inside,
                      patch_cap, target_from_intro, verify_copy, verify_extracted,
                      verify_options, sha)


class FixedBuildGuards(unittest.TestCase):
    original = b'enum : unsigned long { MAX_LINELET_POINTS = 32 }; // cap\n'

    def test_patch_changes_only_cap_digits(self):
        self.assertEqual(patch_cap(self.original), self.original.replace(b'= 32', b'= 256'))

    def test_wrong_duplicate_or_missing_cap_rejected(self):
        for source in (self.original.replace(b'32', b'64'), self.original * 2,
                       b'// MAX_LINELET_POINTS = 32', self.original + b'\nint MAX_LINELET_POINTS=32;'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                patch_cap(source)

    def test_unintended_patch_added_or_missing_file_rejected(self):
        expected = {'a.cpp': {'sha256': 'abc', 'bytes': 3}}
        for actual in ({}, {'a.cpp': {'sha256': 'xyz', 'bytes': 3}},
                       dict(expected, extra={'sha256': 'a', 'bytes': 1})):
            with self.assertRaises(ValueError):
                verify_copy(expected, actual)

    def test_containment_absolute_escape_parent_equality(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(inside(root / 'controls/new/source', root), root / 'controls/new/source')
            for bad in (root, root / '../escape', root.parent / 'other'):
                with self.assertRaises(ValueError):
                    inside(bad, root)

    def test_options_match_and_detect_hidden_optional_toggle(self):
        rows = [{'name': k, 'value': v} for k, v in OPTIONS.items()] + [{'name': 'backend', 'value': 'ninja'}]
        verify_options(rows)
        for key, value in (('with-mpi', 'auto'), ('with-omp', False), ('enable-cgns', True),
                           ('cpu-arch', 'native'), ('wrap_mode', 'default')):
            wrong = [dict(r, value=value) if r['name'] == key else r.copy() for r in rows]
            with self.assertRaises(ValueError):
                verify_options(wrong)
        with self.assertRaises(ValueError):
            verify_options(rows + [rows[0]])
        with self.assertRaises(ValueError):
            verify_options(rows[1:])

    def test_fixed_commands_single_target_and_offline_flags(self):
        root = Path('C:/fixture').resolve()
        cmds = commands(root, root / 'source', root / 'build')
        self.assertEqual(cmds['compile'][-3:], ['-j', '1', 'SU2_CFD/src/SU2_CFD.exe'])
        self.assertIn('-Dcpu-arch=haswell', cmds['configure'])
        self.assertIn('-Dwrap_mode=nodownload', cmds['configure'])
        self.assertEqual(len([x for x in cmds['preconfigure'] if x.startswith('--no-')]), 9)
        self.assertNotIn('--with-own-meson', cmds['preconfigure'])
        self.assertNotIn('install', cmds['compile'])

    def test_windows_target_requires_one_contained_executable(self):
        with tempfile.TemporaryDirectory() as temporary:
            build = Path(temporary)
            row = {'name': 'SU2_CFD', 'type': 'executable', 'filename': [str(build / 'SU2_CFD/src/SU2_CFD.exe')]}
            self.assertEqual(target_from_intro([row], build), 'SU2_CFD/src/SU2_CFD.exe')
            for rows in ([], [row, row], [dict(row, filename=[str(build / '../SU2_CFD.exe')])],
                         [dict(row, filename=[str(build / 'other.exe')])]):
                with self.assertRaises(ValueError):
                    target_from_intro(rows, build)

    def test_archive_safety_rejects_path_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            for index, names in enumerate((['root/../escape'], ['root/a', 'root/A'])):
                archive = Path(temporary) / (str(index) + '.zip')
                with zipfile.ZipFile(archive, 'w') as z:
                    for name in names:
                        z.writestr(name, 'x')
                with self.assertRaises(ValueError):
                    archive_files(archive)

    def test_retained_archive_matches_tree_and_detects_source_edit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'tools/su2-build/v8.5.0'
            folder = home / 'source'
            folder.mkdir(parents=True)
            archive = home / 'fixture.tar.gz'
            with tarfile.open(archive, 'w:gz') as t:
                entry = tarfile.TarInfo('SU2-' + PIN + '/a.cpp')
                entry.size = 3
                t.addfile(entry, io.BytesIO(b'abc'))
            (folder / 'a.cpp').write_bytes(b'abc')
            origin = {'commit': PIN, 'url': 'https://codeload.github.com/su2code/SU2/tar.gz/' + PIN,
                      'path': str(archive.relative_to(root)), 'bytes': archive.stat().st_size,
                      'sha256': sha(archive), 'destination': str(folder.relative_to(root))}
            (folder / 'archive_origin.json').write_text(json.dumps(origin))
            self.assertIn('a.cpp', verify_extracted(root, folder, 'source', PIN)['files'])
            (folder / 'a.cpp').write_bytes(b'bad')
            with self.assertRaises(ValueError):
                verify_extracted(root, folder, 'source', PIN)


if __name__ == '__main__':
    unittest.main(verbosity=2)
