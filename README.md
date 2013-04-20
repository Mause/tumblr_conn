Simple Tumblr Blog Connection Analyzer
======================================
Current implementation follows reblog trails from current user back to source.
Hopefully, i will get the `reblog_path_sink` function in `test_sink.py` working sometime in the future.

Originally built for Google App Engine, on the Python 2.7 platform.
Currently working towards having it run properly on Heroku, python-3.3.0.

As stated in requirements.txt;
 * requests==1.1.0
 * tornado==2.4.1
 * pyzmq==13.0.2

## Implementation details

when i say follow to source, what i mean is this;

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
We are following from the blog specified, so the source; following the reblog trail.

When i say following to the sink, i mean we are traveling in the opposite direction; from the source out.
This is obviously a far more expensive operation, as some posts may have thousands and thousands of blogs having reblogged them.


### License

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
