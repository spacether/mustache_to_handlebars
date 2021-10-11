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
- this tool prints out those nebulous tags so the user can decide which usage it should be
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
Invoke the tool per these options:
mustache_to_handlebars [-h] [-out_dir OUT_DIR] [-handlebars_if_tags HANDLEBARS_IF_TAGS] [-handlebars_each_tags HANDLEBARS_EACH_TAGS]
                              [-handlebars_with_tags HANDLEBARS_WITH_TAGS] [-recursive RECURSIVE] [-delete_in_files DELETE_IN_FILES]
                              in_dir

Note:
handlebars_if_tags/handlebars_each_tags/handlebars_with_tags must be a space delimited list of tags like:
`-handlebars_if_tags='someTag anotherTag'`

## testing
Install pytest in your virtual environment and then run make test