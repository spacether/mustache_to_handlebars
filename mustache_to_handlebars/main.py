import os
import argparse
import glob
import typing
import re
from enum import Enum

HANDLEBARS_EXTENSION = 'handlebars'
HANDLEBARS_IF_CLOSE = '{{/if}}'
HANDLEBARS_UNLESS_CLOSE = '{{/unless}}'
HANDLEBARS_WHITESPACE_REMOVAL_CHAR = '~'
HANDLEBARS_FIRST = '@first'
HANDLEBARS_LAST = '@last'


MUSTACHE_EXTENSION = 'mustache'
MUSTACHE_IF_UNLESS_CLOSE_PATTERN = r'{{([#^/].+?)}}'
MUSTACHE_TO_HANDLEBARS_TAG = {
    '-first': HANDLEBARS_FIRST,
    '-last': HANDLEBARS_LAST
}


class MustacheTagType(str, Enum):
    IF = '#'  # it is unclear if this should be an if(presence) OR each(list iteration) OR with(enter object context)
    UNLESS = '^'
    CLOSE = '/'

def mustache_to_handlebars_tag_element(mustache_tag_element: str) -> str:
    """
    '-first' -> '@first'
    Input excludes the #/^ control characters
    """
    handlebars_tag_element = MUSTACHE_TO_HANDLEBARS_TAG.get(mustache_tag_element)
    if handlebars_tag_element is None:
        return mustache_tag_element
    return handlebars_tag_element

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
        line_ends_in_closing_braces = suffix == end_braces
        try:
            tag_type = MustacheTagType(line[left_brace_count])
            if tag_type and line_ends_in_closing_braces:
                lines[i] = line[:-left_brace_count] + HANDLEBARS_WHITESPACE_REMOVAL_CHAR + suffix
        except ValueError:
            pass
    return '\n'.join(lines)

def _convert_handlebars_to_mustache(in_txt: str) -> typing.Tuple[str, typing.Set[str]]:
    # extract all control tags from {{#someTag}} and {{/someTag}} patterns
    tags = set(re.findall(MUSTACHE_IF_UNLESS_CLOSE_PATTERN, in_txt))
    ambiguous_tags = set()
    if not tags:
        return in_txt, ambiguous_tags
    replacement_index_to_from_to_pair = {}
    closures = []
    for i in range(len(in_txt)):
        for tag_without_braces in tags:
            tag_with_braces = '{{'+tag_without_braces+'}}'

            end_index = i + len(tag_with_braces)
            if end_index > len(in_txt):
                continue
            substr = in_txt[i:i+len(tag_with_braces)]

            if substr == tag_with_braces:
                tag = tag_without_braces[1:]
                tag = mustache_to_handlebars_tag_element(tag)
                if tag not in {HANDLEBARS_FIRST, HANDLEBARS_LAST}:
                    ambiguous_tags.add(tag)
                tag_type = MustacheTagType(tag_without_braces[0])

                if tag_type is MustacheTagType.IF:
                    new_tag = '{{#if ' + tag + '}}'
                    closures.append(HANDLEBARS_IF_CLOSE)
                elif tag_type is MustacheTagType.UNLESS:
                    new_tag = '{{#unless ' + tag + '}}'
                    closures.append(HANDLEBARS_UNLESS_CLOSE)
                elif tag_type is MustacheTagType.CLOSE:
                    new_tag = closures.pop()

                replacement_index_to_from_to_pair[i] = (tag_with_braces, new_tag)
                break


    out_txt = str(in_txt)
    for i, (original_tag, new_tag) in reversed(replacement_index_to_from_to_pair.items()):
        out_txt = out_txt[0:i] + new_tag + out_txt[i+len(original_tag):]

    out_txt = _add_whitespace_handling(out_txt)
    return out_txt, ambiguous_tags

def _create_files(in_path_to_out_path: dict) -> typing.List[str]:
    existing_out_folders = set()
    ambiguous_tags = set()
    input_files_used_to_make_output_files = []
    skipped_files = 0
    for i, (in_path, out_path) in enumerate(in_path_to_out_path.items()):
        print('Reading file {} out of {}, path={}'.format(i+1, len(in_path_to_out_path), in_path))
        with open(in_path) as file:
            in_txt = file.read()

        out_txt, file_ambiguous_tags = _convert_handlebars_to_mustache(in_txt)
        if file_ambiguous_tags:
            ambiguous_tags.update(file_ambiguous_tags)
            skipped_files += 1
            print('Skipped writing file {} because it has ambiguous tags'.format(out_path))
            continue

        out_folder = os.path.dirname(out_path)
        if out_folder not in existing_out_folders:
            if not os.path.isdir(out_folder):
                os.mkdir(out_folder)
            existing_out_folders.add(out_folder)

        with open(out_path, 'w') as file:
            file.write(out_txt)
        input_files_used_to_make_output_files.append(in_path)
        print('Wrote file {}'.format(out_path))

    if ambiguous_tags:
        print('len(ambiguous_tags)={}'.format(len(ambiguous_tags)))
        print('skipped generating {} files'.format(skipped_files))
        print('ambiguous_tags={}'.format(ambiguous_tags))

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
    input_files_used_to_make_output_files = _create_files(in_path_to_out_path)
    if delete_in_files:
        _clean_up_files(input_files_used_to_make_output_files)