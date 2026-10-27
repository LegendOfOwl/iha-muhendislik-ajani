"""Counterexamples for cache recovery, graph scope and native command integrity."""
import unittest
from ninja_recipe import (TARGET, SOURCE, EXTRA_ARG, derive_manifest, windows_arguments,
                          command_map, verify_command_delta, inventory, verify_dry_run)


def manifest(ending='\n'):
    return ending.join(['# Meson marker: preserve me exactly', 'rule cpp_COMPILER',
        ' command = g++ $ARGS -MD -MQ $out -o $out -c $in',
        'build build.ninja: REGENERATE_BUILD ../source/meson.build',
        ' pool = console', '', f'build {TARGET}: cpp_COMPILER {SOURCE}',
        f' DEPFILE = "{TARGET}.d"', f' DEPFILE_UNQUOTED = {TARGET}.d',
        ' ARGS = "-std=c++17" "-O3" "-fopenmp"', '',
        'build lib.a: STATIC_LINKER ' + TARGET, ' LINK_ARGS = "csrDT"', '',
        '# tail marker: immutable', '']).encode()


def compilation(output=TARGET, source=SOURCE, extra=''):
    return (f'"C:\\Compiler Path\\g++.exe" "-std=c++17" "-O3" "-fopenmp"{extra}'
            f' -MD -MQ {output} -MF "{output}.d" -o {output} "-c" {source}')


def commands(extra=''):
    return '\n'.join([compilation('cached.obj', '../source/a.cpp'), compilation(extra=extra),
                       '"gcc-ar" "csrDT" lib.a @lib.a.rsp',
                       '"C:\\Compiler Path\\g++.exe" -o app.exe lib.a "-fopenmp"']) + '\n'


class RecipeTests(unittest.TestCase):
    def test_only_exact_edge_arg_changes_and_markers_keep_bytes(self):
        for newline in ('\n', '\r\n'):
            original = manifest(newline)
            changed = derive_manifest(original)
            self.assertEqual(changed.replace((' "' + EXTRA_ARG + '"').encode(), b'', 1), original)
            self.assertIn(b'build build.ninja: REGENERATE_BUILD ../source/meson.build', changed)
            self.assertTrue(changed.endswith(('# tail marker: immutable' + newline).encode()))

    def test_missing_edge_rejected(self):
        with self.assertRaises(ValueError):
            derive_manifest(manifest().replace(TARGET.encode(), b'other.obj'))

    def test_duplicate_edge_rejected(self):
        with self.assertRaises(ValueError):
            derive_manifest(manifest() + manifest())

    def test_deceptive_source_path_rejected(self):
        with self.assertRaises(ValueError):
            derive_manifest(manifest().replace(SOURCE.encode(), (SOURCE + '.evil').encode()))

    def test_deceptive_target_path_rejected(self):
        with self.assertRaises(ValueError):
            derive_manifest(manifest().replace(TARGET.encode(), ('evil/' + TARGET).encode()))

    def test_duplicate_args_and_edge_command_rejected(self):
        for injection in (b' ARGS = "-O0"\n', b' command = other-compiler\n'):
            with self.assertRaises(ValueError):
                derive_manifest(manifest().replace(b' ARGS = ', injection + b' ARGS = ', 1))

    def test_no_reapplication_or_global_include(self):
        with self.assertRaises(ValueError):
            derive_manifest(derive_manifest(manifest()))
        with self.assertRaises(ValueError):
            derive_manifest(manifest() + ('# ' + EXTRA_ARG).encode())

    def test_variable_expansion_rejected(self):
        with self.assertRaises(ValueError):
            derive_manifest(manifest().replace(b'"-std=c++17"', b'$injected_args'))


class CommandTests(unittest.TestCase):
    def test_windows_parser_preserves_backslashes_and_spaces(self):
        self.assertEqual(windows_arguments('"C:\\Program Files\\g++.exe" "a b" "x\\y"'),
                         ['C:\\Program Files\\g++.exe', 'a b', 'x\\y'])
        self.assertEqual(windows_arguments('app "" "one\\\"two"'), ['app', '', 'one"two'])

    def test_unclosed_quote_rejected(self):
        with self.assertRaises(ValueError):
            windows_arguments('"app')

    def test_expected_delta_and_kind_counts(self):
        new = commands(' "' + EXTRA_ARG + '"')
        delta = verify_command_delta(commands(), new)
        self.assertEqual(delta['changed_outputs'], [TARGET])
        self.assertEqual(delta['unchanged_command_count'], 3)
        index = command_map(new)
        info = inventory(index, {'cached.obj'}, {'cached.obj'})
        self.assertEqual(info['remaining_by_kind'], {'compile': 1, 'archive': 1, 'link': 1})

    def test_additional_flag_change_rejected(self):
        with self.assertRaises(ValueError):
            verify_command_delta(commands(), commands(' "' + EXTRA_ARG + '"').replace('"-O3"', '"-O0"', 1))

    def test_optimization_change_inside_traction_edge_rejected(self):
        before, after = commands(), commands(' "' + EXTRA_ARG + '"')
        after = after.replace(compilation(extra=' "' + EXTRA_ARG + '"'),
                              compilation(extra=' "' + EXTRA_ARG + '"').replace('"-O3"', '"-O0"'))
        with self.assertRaises(ValueError):
            verify_command_delta(before, after)

    def test_duplicate_output_rejected(self):
        with self.assertRaises(ValueError):
            command_map(commands() + compilation('cached.obj', '../source/b.cpp'))

    def test_unrecognized_command_rejected(self):
        with self.assertRaises(ValueError):
            command_map(commands() + '\ncmd /c arbitrary')

    def test_deceptive_output_and_missing_source_rejected(self):
        with self.assertRaises(ValueError):
            command_map(compilation('../cached.obj', '../source/a.cpp'))
        with self.assertRaises(ValueError):
            command_map(compilation().replace(' "-c" ' + SOURCE, ' "-c"'))

    def test_cache_log_disagreement_rejected(self):
        for existing, logged in (({'cached.obj'}, set()), (set(), {'cached.obj'}),
                                  ({TARGET}, {TARGET})):
            with self.assertRaises(ValueError):
                inventory(command_map(commands()), existing, logged)

    def test_dry_run_has_only_missing_outputs(self):
        index = command_map(commands(' "' + EXTRA_ARG + '"'))
        info = inventory(index, {'cached.obj'}, {'cached.obj'})
        planned = [index[x]['command'] for x in info['remaining']]
        dry = "ninja: Entering directory 'build'\n" + '\n'.join(
            f'[{i}/3] {command}' for i, command in enumerate(planned, 1))
        self.assertTrue(verify_dry_run(index, info, dry)['passed'])

    def test_dry_run_cache_recompile_rejected(self):
        index = command_map(commands())
        info = inventory(index, {'cached.obj'}, {'cached.obj'})
        dry = '\n'.join(f'[{i}/4] {x["command"]}' for i, x in enumerate(index.values(), 1))
        with self.assertRaises(ValueError):
            verify_dry_run(index, info, dry)

    def test_dry_run_missing_step_rejected(self):
        index = command_map(commands())
        info = inventory(index, {'cached.obj'}, {'cached.obj'})
        dry = '[1/3] ' + index[TARGET]['command']
        with self.assertRaises(ValueError):
            verify_dry_run(index, info, dry)


if __name__ == '__main__':
    unittest.main(verbosity=2)
