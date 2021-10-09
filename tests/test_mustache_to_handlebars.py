import glob
import os
import unittest

import mustache_to_handlebars.main as main

class TestHelpers(unittest.TestCase):
    in_dir = os.path.join('tests', 'in_dir')

    def test_get_in_file_to_out_file_map_not_recursive(self):
        in_file_to_out_file_map = main._get_in_file_to_out_file_map(
            in_dir=self.in_dir, out_dir=self.in_dir, recursive=False)

        self.assertEqual(
            in_file_to_out_file_map,
            {
                'tests/in_dir/api.mustache': 'tests/in_dir/api.handlebars',
                'tests/in_dir/partial_header.mustache': 'tests/in_dir/partial_header.handlebars'
            }
        )

    def test_get_in_file_to_out_file_map_recursive(self):
        in_file_to_out_file_map = main._get_in_file_to_out_file_map(
            in_dir=self.in_dir, out_dir=self.in_dir, recursive=True)

        self.assertEqual(
            in_file_to_out_file_map,
            {
                'tests/in_dir/api.mustache': 'tests/in_dir/api.handlebars',
                'tests/in_dir/model_templates/imports.mustache': 'tests/in_dir/model_templates/imports.handlebars',
                'tests/in_dir/partial_header.mustache': 'tests/in_dir/partial_header.handlebars'
            }
        )

    def test_create_files(self):
        in_file_to_out_file_map = main._get_in_file_to_out_file_map(
            in_dir=self.in_dir, out_dir=self.in_dir, recursive=False)
        main._create_files(
            in_file_to_out_file_map,
            {main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST},
            set(),
            set(),
        )
        in_handebars_path_pattern = os.path.join('tests', 'in_dir', '*.{}'.format(main.HANDLEBARS_EXTENSION))
        handlebars_files = glob.glob(in_handebars_path_pattern, recursive=False)
        self.assertEqual(
            set(in_file_to_out_file_map.values()),
            set(handlebars_files)
        )
        main._clean_up_files(handlebars_files)

    def test_convert_handlebars_to_mustache_with_ambiguous_tags(self):
        in_txt = '\n'.join([
            '{{#a}}{{#b}}',
            '{{#someList}}',
            '  {{#otherList}}',
            '{{#c}}{{#c}}{{/c}}{{/c}}',
            '{{#-first}}',
            '{{/-first}}',
            '{{#-last}}',
            '{{/-last}}',
            '{{^-first}}',
            '{{/-first}}',
            '{{^-last}}',
            '{{/-last}}',
            '  {{/otherList}}',
            '{{/someList}}',
            '{{/b}}{{/a}}'
        ])
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            {main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST},
            set(),
            set(),
        )
        expected_out_txt = '\n'.join([
            '{{#ifOrEachOrWith a}}{{#ifOrEachOrWith b}}',
            '{{#ifOrEachOrWith someList~}}',
            '  {{#ifOrEachOrWith otherList}}',
            '{{#ifOrEachOrWith c}}{{#ifOrEachOrWith c}}{{/ifOrEachOrWith}}{{/ifOrEachOrWith}}',
            '{{#if @first~}}',
            '{{/if~}}',
            '{{#if @last~}}',
            '{{/if~}}',
            '{{#unless @first~}}',
            '{{/unless~}}',
            '{{#unless @last~}}',
            '{{/unless~}}',
            '  {{/ifOrEachOrWith}}',
            '{{/ifOrEachOrWith~}}',
            '{{/ifOrEachOrWith}}{{/ifOrEachOrWith}}',
        ])
        expected_ambiguous_tags = {'b', 'someList', 'otherList', 'a', 'c'}
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

    def test_convert_handlebars_to_mustache_no_ambiguous_tags(self):
        in_txt = '\n'.join([
            '{{#a}}{{#b}}',
            '{{#someList}}',
            '  {{#otherList}}',
            '{{#c}}{{#c}}{{/c}}{{/c}}',
            '{{#-first}}',
            '{{/-first}}',
            '{{#-last}}',
            '{{/-last}}',
            '{{^-first}}',
            '{{/-first}}',
            '{{^-last}}',
            '{{/-last}}',
            '  {{/otherList}}',
            '{{/someList}}',
            '{{/b}}{{/a}}'
        ])
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            {main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST, 'a', 'b'},
            {'someList', 'otherList'},
            {'c'},
        )
        expected_out_txt = '\n'.join([
            '{{#if a}}{{#if b}}',
            '{{#each someList~}}',
            '  {{#each otherList}}',
            '{{#with c}}{{#with c}}{{/with}}{{/with}}',
            '{{#if @first~}}',
            '{{/if~}}',
            '{{#if @last~}}',
            '{{/if~}}',
            '{{#unless @first~}}',
            '{{/unless~}}',
            '{{#unless @last~}}',
            '{{/unless~}}',
            '  {{/each}}',
            '{{/each~}}',
            '{{/if}}{{/if}}',
        ])
        expected_ambiguous_tags = set()
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

if __name__ == '__main__':
    unittest.main()