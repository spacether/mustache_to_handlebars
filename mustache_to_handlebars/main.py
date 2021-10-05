import os
import argparse
import glob


MUSTACHE_EXTENSION = 'mustache'
HANDLEBARS_EXTENSION = 'handlebars'

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def __get_args():
    parser = argparse.ArgumentParser(description='convert templates from mustache to handebars')
    parser.add_argument('in_dir', type=dir_path)
    parser.add_argument('-out_dir', type=str)
    parser.add_argument('-recursive', type=bool, default=True)
    parser.add_argument('-delete_in_files', type=bool, default=False)
    args = parser.parse_args()
    return args.in_dir, args.out_dir, args.recursive, args.delete_in_files

def _get_in_file_to_out_file_map(in_dir: str, out_dir: str, recursive: bool) -> dict:
    path_args = []
    if recursive:
        path_args.append('**')
    path_args.append('*.{}'.format(MUSTACHE_EXTENSION))
    in_dir_mustache_path_pattern = os.path.join(in_dir, *path_args)

    mustache_files = glob.glob(in_dir_mustache_path_pattern, recursive=recursive)

    in_path_to_out_path = {}
    for full_path in mustache_files:
        path_from_dir = os.path.relpath(full_path, in_dir)
        path_from_dir = path_from_dir.replace(MUSTACHE_EXTENSION, HANDLEBARS_EXTENSION)
        out_path = os.path.join(out_dir, path_from_dir)
        in_path_to_out_path[full_path] = out_path
    return in_path_to_out_path

def _create_files(in_path_to_out_path: dict):
    existing_out_folders = set()
    for i, (in_path, out_path) in enumerate(in_path_to_out_path.items()):
        print('Reading file {} out of {}, path={}'.format(i+1, len(in_path_to_out_path), in_path))
        with open(in_path) as file:
            lines = file.readlines()
            lines = [line.rstrip() for line in lines]

        full_txt = '\n'.join(lines)
        out_folder = os.path.dirname(out_path)
        if out_folder not in existing_out_folders:
            if not os.path.isdir(out_folder):
                os.mkdir(out_folder)
            existing_out_folders.add(out_folder)

        with open(out_path, 'w') as file:
            file.write(full_txt)
        print('Wrote file {}'.format(out_path))

def __clean_up_files(in_path_to_out_path: dict, delete_in_files: bool):
    if not delete_in_files:
        print('Original templates have not been deleted')
        return
    for i, in_path in enumerate(in_path_to_out_path):
        print('Removing file {} out of {}, path={}'.format(i+1, len(in_path_to_out_path), in_path))
        os.remove(in_path)


def mustache_to_handlebars():
    in_dir, out_dir, recursive, delete_in_files = __get_args()
    if not out_dir:
        out_dir = in_dir

    in_path_to_out_path = _get_in_file_to_out_file_map(in_dir, out_dir, recursive)
    _create_files(in_path_to_out_path)
    __clean_up_files(in_path_to_out_path, delete_in_files)