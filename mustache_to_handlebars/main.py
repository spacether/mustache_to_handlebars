import os
import argparse
import glob
import typing
import re
from enum import Enum

TAG_OPEN = '{{'
TAG_CLOSE = '}}'
HANDLEBARS_EXTENSION = 'handlebars'
HANDLEBARS_WHITESPACE_REMOVAL_CHAR = '~'
HANDLEBARS_FIRST = '@first'
HANDLEBARS_LAST = '@last'


MUSTACHE_EXTENSION = 'mustache'
MUSTACHE_IF_UNLESS_CLOSE_PATTERN = r'{{([#^/].+?)}}'
MUSTACHE_TO_HANDLEBARS_TAG = {
    '-first': HANDLEBARS_FIRST,
    '-last': HANDLEBARS_LAST
}


HANDLEBARS_IF_TAGS = {HANDLEBARS_FIRST, HANDLEBARS_LAST}
HANDLEBARS_EACH_TAGS = set()
HANDLEBARS_WITH_TAGS = set()

class MustacheTagType(str, Enum):
    IF_EACH_WITH = '#'  # it is unclear if this should be an if(presence) OR each(list iteration) OR with(enter object context)
    UNLESS = '^'
    CLOSE = '/'

class HandlebarsTagType(Enum):
    # value is open prefix, close tag
    IF = ('#if', '/if')
    EACH = ('#each', '/each')
    WITH = ('#with', '/with')
    UNLESS = ('#unless', '/unless')
    CLOSE = ('', '')

def __get_handlebars_tag_type(
    tag: str,
    mustache_tag_control_character: str,
    handlebars_if_tags: typing.Set[str],
    handlebars_each_tags: typing.Set[str],
    handlebars_with_tags: typing.Set[str]
) -> typing.Optional[HandlebarsTagType]:
    # mustache_tag_control_character: the #/^ control character
    mustache_tag_type = MustacheTagType(mustache_tag_control_character)
    if mustache_tag_type is MustacheTagType.IF_EACH_WITH:
        if tag in handlebars_if_tags:
            return HandlebarsTagType.IF
        if tag in handlebars_each_tags:
            return HandlebarsTagType.EACH
        if tag in handlebars_with_tags:
            return HandlebarsTagType.WITH
    elif mustache_tag_type is MustacheTagType.UNLESS:
        return HandlebarsTagType.UNLESS
    elif mustache_tag_type is MustacheTagType.CLOSE:
        return HandlebarsTagType.CLOSE
    return None

def __mustache_to_handlebars_tag_element(mustache_tag_element: str) -> str:
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

def _convert_handlebars_to_mustache(
    in_txt: str,
    handlebars_if_tags: typing.Set[str],
    handlebars_each_tags: typing.Set[str],
    handlebars_with_tags: typing.Set[str]
) -> typing.Tuple[str, typing.Set[str]]:
    # extract all control tags from {{#someTag}} and {{/someTag}} patterns
    tags = set(re.findall(MUSTACHE_IF_UNLESS_CLOSE_PATTERN, in_txt))
    ambiguous_tags = set()
    if not tags:
        return in_txt, ambiguous_tags
    replacement_index_to_from_to_pair = {}
    closures = []
    for i in range(len(in_txt)):
        for tag_without_braces in tags:
            tag_with_braces = TAG_OPEN + tag_without_braces + TAG_CLOSE

            end_index = i + len(tag_with_braces)
            if end_index > len(in_txt):
                continue
            substr = in_txt[i:i+len(tag_with_braces)]

            if substr == tag_with_braces:
                tag = tag_without_braces[1:]
                tag = __mustache_to_handlebars_tag_element(tag)
                handlebars_tag_type = __get_handlebars_tag_type(
                    tag,
                    tag_without_braces[0],
                    handlebars_if_tags,
                    handlebars_each_tags,
                    handlebars_with_tags
                )

                if (
                    handlebars_tag_type in
                    {HandlebarsTagType.IF, HandlebarsTagType.EACH, HandlebarsTagType.WITH, HandlebarsTagType.UNLESS}
                ):
                    new_tag = TAG_OPEN + handlebars_tag_type.value[0] + ' ' + tag + TAG_CLOSE
                    closures.append(handlebars_tag_type.value[1])
                elif handlebars_tag_type is None:
                    ambiguous_tags.add(tag)
                    new_tag = '{{#ifOrEachOrWith ' + tag + TAG_CLOSE
                    closures.append('/ifOrEachOrWith')
                elif handlebars_tag_type is HandlebarsTagType.CLOSE:
                    new_tag = TAG_OPEN + closures.pop() + TAG_CLOSE

                replacement_index_to_from_to_pair[i] = (tag_with_braces, new_tag)
                break

    out_txt = str(in_txt)
    for i, (original_tag, new_tag) in reversed(replacement_index_to_from_to_pair.items()):
        out_txt = out_txt[0:i] + new_tag + out_txt[i+len(original_tag):]

    out_txt = _add_whitespace_handling(out_txt)
    return out_txt, ambiguous_tags

def _create_files(in_path_to_out_path: dict) -> typing.Tuple[typing.List[str], typing.Set[str]]:
    existing_out_folders = set()
    ambiguous_tags = set()
    input_files_used_to_make_output_files = []
    for i, (in_path, out_path) in enumerate(in_path_to_out_path.items()):
        print('Reading file {} out of {}, path={}'.format(i+1, len(in_path_to_out_path), in_path))
        with open(in_path) as file:
            in_txt = file.read()

        out_txt, file_ambiguous_tags = _convert_handlebars_to_mustache(in_txt, HANDLEBARS_IF_TAGS, HANDLEBARS_EACH_TAGS, HANDLEBARS_WITH_TAGS)
        if file_ambiguous_tags:
            ambiguous_tags.update(file_ambiguous_tags)
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
    return input_files_used_to_make_output_files, ambiguous_tags

def _clean_up_files(files_to_delete: typing.List[str]):
    if not files_to_delete:
        print('Original templates have not been deleted')
        return
    for i, path in enumerate(files_to_delete):
        print('Removing file {} out of {}, path={}'.format(i+1, len(files_to_delete), path))
        os.remove(path)

def __handle_ambiguous_tags(ambiguous_tags: typing.Set[str], qty_skipped_files: int):
    print('\nskipped generating {} files'.format(qty_skipped_files))
    print('qty_ambiguous_tags={}'.format(len(ambiguous_tags)))
    print('ambiguous_tags={}'.format(ambiguous_tags))

    suspected_if_tags = []
    suspected_each_tags = []
    for tag in ambiguous_tags:
        if (
            tag.startswith('is') or
            tag.startswith('has') or
            tag.startswith('getHas') or
            tag.startswith('use') or
            tag.startswith('getIs')
        ):
            suspected_if_tags.append(tag)
    ambiguous_tags = ambiguous_tags - set(suspected_if_tags)
    for tag in ambiguous_tags:
        if tag.endswith('s'):
            suspected_each_tags.append(tag)
    ambiguous_tags = ambiguous_tags - set(suspected_each_tags)
    suspected_with_tags = list(ambiguous_tags)
    print('here are some guesses at what your tags may be based only on tag names:\n')
    print('if_tags=\"{}\"\n'.format(" ".join(suspected_if_tags)))
    print('each_tags=\"{}\"\n'.format(" ".join(suspected_each_tags)))
    print('with_tags=\"{}\"\n'.format(" ".join(suspected_with_tags)))


def mustache_to_handlebars():
    in_dir, out_dir, recursive, delete_in_files = __get_args()
    if not out_dir:
        out_dir = in_dir

    in_path_to_out_path = _get_in_file_to_out_file_map(in_dir, out_dir, recursive)
    input_files_used_to_make_output_files, ambiguous_tags = _create_files(in_path_to_out_path)

    if ambiguous_tags:
        __handle_ambiguous_tags(
            ambiguous_tags,
            len(in_path_to_out_path) - len(input_files_used_to_make_output_files)
        )

    if delete_in_files:
        _clean_up_files(input_files_used_to_make_output_files)