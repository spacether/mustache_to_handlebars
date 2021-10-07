import os
import argparse
import glob
import typing


MUSTACHE_EXTENSION = 'mustache'
MUSTACHE_FIRST_CLOSE = '{{/-first}}'
MUSTACHE_LAST_CLOSE = '{{/-last}}'
MUSTACHE_IF_FIRST = '{{#-first}}'
MUSTACHE_IF_LAST = '{{#-last}}'
MUSTACHE_UNLESS_FIRST = '{{^-first}}'
MUSTACHE_UNLESS_LAST = '{{^-last}}'

HANDLEBARS_EXTENSION = 'handlebars'
HANDLEBARS_IF_FIRST = '{{#if @first}}'
HANDLEBARS_IF_LAST = '{{#if @last}}'
HANDLEBARS_UNLESS_FIRST = '{{#unless @first}}'
HANDLEBARS_UNLESS_LAST = '{{#unless @last}}'
HANDLEBARS_IF_CLOSE = '{{/if}}'
HANDLEBARS_UNLESS_CLOSE = '{{/unless}}'
HANDLEBARS_WHITESPACE_REMOVAL_CHAR = '~'
CONTROL_CHARS = {'#', '/', '^'}

REPLACEMENTS = {
    MUSTACHE_IF_FIRST: lambda x: HANDLEBARS_IF_FIRST,
    MUSTACHE_IF_LAST: lambda x: HANDLEBARS_IF_LAST,
    MUSTACHE_UNLESS_FIRST: lambda x: HANDLEBARS_UNLESS_FIRST,
    MUSTACHE_UNLESS_LAST: lambda x: HANDLEBARS_UNLESS_LAST,
    MUSTACHE_FIRST_CLOSE: lambda x: x.pop(),  # may be replaced with '{{\if}}' OR '{{\unless}}'
    MUSTACHE_LAST_CLOSE: lambda x: x.pop(),  # may be replaced with '{{\if}}' OR '{{\unless}}'
}

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
        ends_in_closing_braces = suffix == end_braces
        tag_is_helper = line[left_brace_count] in CONTROL_CHARS
        if tag_is_helper and ends_in_closing_braces:
            lines[i] = line[:-left_brace_count] + HANDLEBARS_WHITESPACE_REMOVAL_CHAR + suffix
    return '\n'.join(lines)


def _convert_handlebars_to_mustache(in_txt: str) -> str:
    replacement_index_to_from_to_pair = {}
    closures = []
    for i in range(len(in_txt)):
        for original_tag, new_tag_getter_fn in REPLACEMENTS.items():
            end_index = i + len(original_tag)
            if end_index > len(in_txt):
                continue
            substr = in_txt[i:i+len(original_tag)]
            if substr == original_tag:
                new_tag_getter_fn_input = None
                if original_tag in {MUSTACHE_IF_FIRST, MUSTACHE_IF_LAST}:
                    closures.append(HANDLEBARS_IF_CLOSE)
                elif original_tag in {MUSTACHE_UNLESS_FIRST, MUSTACHE_UNLESS_LAST}:
                    closures.append(HANDLEBARS_UNLESS_CLOSE)
                elif original_tag in {MUSTACHE_FIRST_CLOSE, MUSTACHE_LAST_CLOSE}:
                    new_tag_getter_fn_input = closures

                new_tag = new_tag_getter_fn(new_tag_getter_fn_input)
                replacement_index_to_from_to_pair[i] = (original_tag, new_tag)
                break

    out_txt = str(in_txt)
    for i, (original_tag, new_tag) in reversed(replacement_index_to_from_to_pair.items()):
        out_txt = out_txt[0:i] + new_tag + out_txt[i+len(original_tag):]

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