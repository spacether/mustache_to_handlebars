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
        main._create_files(in_file_to_out_file_map)
        in_handebars_path_pattern = os.path.join('tests', 'in_dir', '*.{}'.format(main.HANDLEBARS_EXTENSION))
        handlebars_files = glob.glob(in_handebars_path_pattern, recursive=False)
        self.assertEqual(
            set(in_file_to_out_file_map.values()),
            set(handlebars_files)
        )

if __name__ == '__main__':
    unittest.main()