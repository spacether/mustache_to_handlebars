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

    def test_get_mustache_partial_paths(self):
        in_file_to_out_file_map = {
            'tests/in_dir/api.mustache': 'tests/in_dir/api.handlebars',
            'tests/in_dir/model_templates/imports.mustache': 'tests/in_dir/model_templates/imports.handlebars',
            'tests/in_dir/partial_header.mustache': 'tests/in_dir/partial_header.handlebars'
        }

        mustache_partial_paths = main._get_mustache_partial_paths(in_file_to_out_file_map, self.in_dir)
        self.assertEqual(
            mustache_partial_paths,
            {'tests/in_dir/partial_header.mustache'}
        )


    def test_create_files(self):
        in_file_to_out_file_map = main._get_in_file_to_out_file_map(
            in_dir=self.in_dir, out_dir=self.in_dir, recursive=False)
        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST},
            each_tags=set(),
            with_tags=set()
        )
        whitespace_config = main.HandlebarsWhitespaceConfig()
        main._create_files(
            in_file_to_out_file_map, handlebars_tag_set, whitespace_config
        )
        in_handebars_path_pattern = os.path.join('tests', 'in_dir', '*.{}'.format(main.HANDLEBARS_EXTENSION))
        handlebars_files = glob.glob(in_handebars_path_pattern, recursive=False)
        self.assertEqual(
            set(in_file_to_out_file_map.values()),
            set(handlebars_files)
        )
        main._clean_up_files(handlebars_files)

    def test_convert_handlebars_to_mustache_if_unless_first_last(self):
        in_txt = '\n'.join([
            '{{#-first}}',
            '{{/-first}}',
            '{{#-last}}',
            '{{/-last}}',
            '{{^-first}}',
            '{{/-first}}',
            '{{^-last}}',
            '{{/-last}}',
        ])
        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST},
            each_tags=set(),
            with_tags=set()
        )
        whitespace_config = main.HandlebarsWhitespaceConfig()
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            whitespace_config
        )
        expected_out_txt = '\n'.join([
            '{{#if @first}}',
            '{{/if}}',
            '{{#if @last}}',
            '{{/if}}',
            '{{#unless @first}}',
            '{{/unless}}',
            '{{#unless @last}}',
            '{{/unless}}',
        ])
        expected_ambiguous_tags = set()
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

    def test_convert_handlebars_to_mustache_tag_whitespace_config(self):
        in_txt = '\n'.join([
            '{{#a}}',
            '{{/a}}',
        ])

        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST, 'a'},
            each_tags=set(),
            with_tags=set()
        )
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            main.HandlebarsWhitespaceConfig(
                remove_whitespace_before_open=True
            )
        )
        expected_out_txt = '\n'.join([
            '{{~#if a}}',
            '{{/if}}',

        ])
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, set())

        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            main.HandlebarsWhitespaceConfig(
                remove_whitespace_after_open=True
            )
        )
        expected_out_txt = '\n'.join([
            '{{#if a~}}',
            '{{/if}}',

        ])
        self.assertEqual(
            out_txt, expected_out_txt)

        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            main.HandlebarsWhitespaceConfig(
                remove_whitespace_before_close=True
            )
        )
        expected_out_txt = '\n'.join([
            '{{#if a}}',
            '{{~/if}}',

        ])
        self.assertEqual(
            out_txt, expected_out_txt)

        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            main.HandlebarsWhitespaceConfig(
                remove_whitespace_after_close=True
            )
        )
        expected_out_txt = '\n'.join([
            '{{#if a}}',
            '{{/if~}}',

        ])
        self.assertEqual(
            out_txt, expected_out_txt)

    def test_convert_handlebars_to_mustache_tag_in_tag(self):
        in_txt = '\n'.join([
            '{{#a}}{{#a}}{{/a}}{{/a}}',
        ])

        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST, 'a'},
            each_tags=set(),
            with_tags=set()
        )
        whitespace_config = main.HandlebarsWhitespaceConfig()
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            whitespace_config
        )
        expected_out_txt = '\n'.join([
            '{{#if a}}{{#if a}}{{/if}}{{/if}}',

        ])
        expected_ambiguous_tags = set()
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

    def test_convert_handlebars_to_mustache_with_ambiguous_tags(self):
        in_txt = '\n'.join([
            '{{#a}}{{#b}}',
            '{{#someList}}',
            '  {{#otherList}}',
            '  {{/otherList}}',
            '{{/someList}}',
            '{{/b}}{{/a}}'
        ])
        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST},
            each_tags=set(),
            with_tags=set()
        )
        whitespace_config = main.HandlebarsWhitespaceConfig()
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            whitespace_config
        )
        expected_out_txt = '\n'.join([
            '{{#ifOrEachOrWith a}}{{#ifOrEachOrWith b}}',
            '{{#ifOrEachOrWith someList}}',
            '  {{#ifOrEachOrWith otherList}}',
            '  {{/ifOrEachOrWith}}',
            '{{/ifOrEachOrWith}}',
            '{{/ifOrEachOrWith}}{{/ifOrEachOrWith}}',
        ])
        expected_ambiguous_tags = {'b', 'someList', 'otherList', 'a'}
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

    def test_convert_handlebars_to_mustache_no_ambiguous_tags(self):
        in_txt = '\n'.join([
            '{{#a}}{{#b}}',
            '{{#someList}}',
            '  {{#otherList}}',
            '  {{/otherList}}',
            '{{/someList}}',
            '{{/b}}{{/a}}'
        ])
        handlebars_tag_set = main.HandlebarTagSet(
            if_tags={main.HANDLEBARS_FIRST, main.HANDLEBARS_LAST, 'a'},
            each_tags={'someList', 'otherList'},
            with_tags={'b'}
        )
        whitespace_config = main.HandlebarsWhitespaceConfig()
        out_txt, ambiguous_tags = main._convert_handlebars_to_mustache(
            in_txt,
            handlebars_tag_set,
            whitespace_config
        )
        expected_out_txt = '\n'.join([
            '{{#if a}}{{#with b}}',
            '{{#each someList}}',
            '  {{#each otherList}}',
            '  {{/each}}',
            '{{/each}}',
            '{{/with}}{{/if}}',
        ])
        expected_ambiguous_tags = set()
        self.assertEqual(
            out_txt, expected_out_txt)
        self.assertEqual(
            ambiguous_tags, expected_ambiguous_tags)

if __name__ == '__main__':
    unittest.main()