import os
import argparse
import glob
import typing


MUSTACHE_EXTENSION = 'mustache'
HANDLEBARS_EXTENSION = 'handlebars'

HANDLBARS_IF_FIRST_TAG = '{{#if @first}}'
HANDLBARS_IF_LAST_TAG = '{{#if @last}}'
HANDLBARS_UNLESS_FIRST_TAG = '{{#unless @first}}'
HANDLBARS_UNLESS_LAST_TAG = '{{#unless @last}}'
HANDLBARS_IF_CLOSE = '{{/if}}'
HANDLBARS_UNLESS_CLOSE = '{{/unless}}'
HANDLEBARS_WHITESPACE_REMOVAL_CHAR = '~'

REPLACEMENTS = {
    '{{#-first}}': HANDLBARS_IF_FIRST_TAG,
    '{{#-last}}': HANDLBARS_IF_LAST_TAG,
    '{{^-first}}': HANDLBARS_UNLESS_FIRST_TAG,
    '{{^-last}}': HANDLBARS_UNLESS_LAST_TAG,
}

MUSTACHE_FIRST_CLOSE_TAG = '{{/-first}}'  # may be replaced with '{{\if}}' OR '{{\unless}}'
MUSTACHE_LAST_CLOSE_TAG = '{{/-last}}'  # may be replaced with '{{\if}}' OR '{{\unless}}'

def __dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def __get_args():
    parser = argparse.ArgumentParser(description='convert templates from mustache to handebars')
    parser.add_argument('in_dir', type=__dir_path)
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


def __replace_first_or_last_close_tag(tag_to_replace: str, if_open_tag: str, unless_open_tag: str, in_txt: str) -> str:
    txt_pieces = in_txt.split(tag_to_replace)
    out_txt = ''
    for i, txt_piece in enumerate(txt_pieces):
        out_txt += txt_piece
        if i == len(txt_pieces) - 1 or len(txt_pieces) == 1:
            continue
        # look back for if or unless
        if_index = txt_piece.find(if_open_tag)
        unless_index = txt_piece.find(unless_open_tag)
        if if_index > unless_index:
            out_txt += HANDLBARS_IF_CLOSE
        else:
            out_txt += HANDLBARS_UNLESS_CLOSE
    return out_txt

def _add_whitespace_handling(in_txt: str) -> str:
    lines = in_txt.split('\n')
    for i, line in enumerate(lines):
        left_brace_count = line.count('{')
        right_brace_count = line.count('{')
        if left_brace_count != right_brace_count:
            continue
        if left_brace_count <= 1 or left_brace_count > 3:
            continue
        tag_open_count = line.count('{'*left_brace_count)
        if not tag_open_count:
            continue
        end_braces = '}'*left_brace_count
        tag_close_count = line.count(end_braces)
        if not tag_close_count:
            continue
        # there is only one tag on this line
        suffix = line[-left_brace_count:]
        if suffix == end_braces:
            lines[i] = line[:-left_brace_count] + HANDLEBARS_WHITESPACE_REMOVAL_CHAR + suffix
    return '\n'.join(lines)


def _convert_handlebars_to_mustache(in_txt: str) -> str:
    out_txt = str(in_txt)
    for original_tag, new_tag in REPLACEMENTS.items():
        out_txt = out_txt.replace(original_tag, new_tag)
    out_txt = __replace_first_or_last_close_tag(
        MUSTACHE_FIRST_CLOSE_TAG, HANDLBARS_IF_FIRST_TAG, HANDLBARS_UNLESS_FIRST_TAG, out_txt)
    out_txt = __replace_first_or_last_close_tag(
        MUSTACHE_LAST_CLOSE_TAG, HANDLBARS_IF_LAST_TAG, HANDLBARS_UNLESS_LAST_TAG, out_txt)
    out_txt = _add_whitespace_handling(out_txt)
    return out_txt

def _create_files(in_path_to_out_path: dict):
    existing_out_folders = set()
    for i, (in_path, out_path) in enumerate(in_path_to_out_path.items()):
        print('Reading file {} out of {}, path={}'.format(i+1, len(in_path_to_out_path), in_path))
        with open(in_path) as file:
            in_txt = file.read()

        out_txt = _convert_handlebars_to_mustache(in_txt)
        out_folder = os.path.dirname(out_path)
        if out_folder not in existing_out_folders:
            if not os.path.isdir(out_folder):
                os.mkdir(out_folder)
            existing_out_folders.add(out_folder)

        with open(out_path, 'w') as file:
            file.write(out_txt)
        print('Wrote file {}'.format(out_path))

def _clean_up_files(files_to_delete: typing.List[str]):
    if not files_to_delete:
        print('Original templates have not been deleted')
        return
    for i, path in enumerate(files_to_delete):
        print('Removing file {} out of {}, path={}'.format(i+1, len(files_to_delete), path))
        os.remove(path)


def mustache_to_handlebars():
    in_dir, out_dir, recursive, delete_in_files = __get_args()
    if not out_dir:
        out_dir = in_dir

    in_path_to_out_path = _get_in_file_to_out_file_map(in_dir, out_dir, recursive)
    _create_files(in_path_to_out_path)
    if delete_in_files:
        _clean_up_files(list(in_path_to_out_path.keys()))