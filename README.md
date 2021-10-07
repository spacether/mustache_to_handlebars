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

Handles adding whitespace characters at the end of tags when
- single tags are used on a template line + the tag is an if or unless tag

## testing
Install pytest in your virtual environment and then run make test