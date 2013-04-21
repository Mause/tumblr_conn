Simple Tumblr Blog Connection Analyzer
======================================

## Please note, this is currently not functional.
Lots of changes and having to re-implement some stuff from;
 * Google App Engine -> Heroku
 * Python 2.7 -> Python 3.3
 * webapp -> tornado


Current implementation follows reblog trails from current user back to source.
Hopefully, I will get the `reblog_path_sink` function in `test_sink.py` working sometime in the future.

Originally built for Google App Engine, on the Python 2.7 platform.
Currently working towards having it run properly on Heroku, python-3.3.0.

As stated in requirements.txt;
 * requests==1.1.0
 * tornado==2.4.1
 * pyzmq==13.0.2
Though whether or not the final implementation will use pyzmq is... debatable.

## Implementation details

Using this as reference;

```
 * source
 |
 * reblogger
 |
 * another reblogger
 |
 * yet another
 |
 * blog from which we start
```
When I say follow to the source, I mean we are following from the blog specified, to the source; following the reblog trail.

When I say following to the sink, I mean we are traveling in the opposite direction; from the source out.
This is obviously a far more expensive operation, as some posts may have thousands and thousands of blogs having reblogged them.


## License

Copyright 2012 Dominic May

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
