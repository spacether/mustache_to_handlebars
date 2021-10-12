# mustache_to_handlebars
A python tool to convert mustache templates to handlebars

This assumes that the specific implementations are:
- mustache: (Java) artifactId=jmustache https://github.com/samskivert/jmustache
- handlebars: (Java) artifactId=handlebars https://github.com/jknack/handlebars.java

### Features
Handles conversion for if/unless first + last
- {{#-first}} -> {{#if @first}}
- {{#-last}} -> {{#if @last}}
- {{^-first}} -> {{#unless @first}}
- {{^-last}} -> {{#unless @last}}
- {{/-first}} -> {{\if}} OR {{\unless}}
- {{/-last}} -> {{\if}} OR {{\unless}}

Tags that begin with # are ambiguous when going from mustache to handlebars because
in mustache, # handles, truthy input, array input, and object context input.
So in handlebars, a mustache #someTag can be #if someTag, #each someTag, or #with someTag
- this tool prints out those ambiguous tags so the user can decide which usage it should be
- one can assign those tags to the if/each/with use cases with the command line arguments
  - -handlebars_if_tags
  - -handlebars_each_tags
  - -handlebars_with_tags

## Usage
Clone this repo
```
# make the virtual env
python3 -m venv venv
# activate it
venv bin/activate
# install the tool into it
make install
```
Invocations:
```
usage: mustache_to_handlebars [-h] [-out_dir OUT_DIR] [-handlebars_if_tags HANDLEBARS_IF_TAGS] [-handlebars_each_tags HANDLEBARS_EACH_TAGS]
                              [-handlebars_with_tags HANDLEBARS_WITH_TAGS] [-remove_whitespace_before_open] [-remove_whitespace_after_open]
                              [-remove_whitespace_before_close] [-remove_whitespace_after_close] [-only_in_dir] [-delete_in_files]
                              in_dir

convert templates from mustache to handebars

positional arguments:
  in_dir                the folder containing your mustache templates

optional arguments:
  -h, --help            show this help message and exit
  -out_dir OUT_DIR      the folder to write the handlebars templates to. if unset in_dir will be used
  -handlebars_if_tags HANDLEBARS_IF_TAGS
                        a list of tags passed in a space delimited string like 'someTag anotherTag'
  -handlebars_each_tags HANDLEBARS_EACH_TAGS
                        a list of tags passed in a space delimited string like 'someTag anotherTag'
  -handlebars_with_tags HANDLEBARS_WITH_TAGS
                        a list of tags passed in a space delimited string like 'someTag anotherTag'
  -remove_whitespace_before_open
  -remove_whitespace_after_open
  -remove_whitespace_before_close
  -remove_whitespace_after_close
  -only_in_dir          the program recurses through descendant directories by default, to only search in_dir, set this parameter
  -delete_in_files      if passed, the mustache template files will be deleted
```

## testing
Install pytest in your virtual environment and then run make test