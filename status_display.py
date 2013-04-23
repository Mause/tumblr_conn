#!/usr/bin/env python
#
# Copyright 2012 Dominic May
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# stdlib
import sys
import time

# third party
import requests

argv = sys.argv[1:]
blog_name = argv[0] if len(argv) > 0 else 'mause-me'


print('Tracing the blog "{}"\n'.format(blog_name))

r = requests.get(
    'http://tumblr-conn.appspot.com/ajax/%s/mapping/status' % blog_name)

if r.json()['queue_len'] == 0:
    print('Post queue is empty.')

if not r.json()['running']:
    print('Not running. Displaying statistics from last analysis.\n')


if float(r.json()['starttime']) != 0:
    print('Analysis began at %s' % r.json['starttime'])

    if r.json()['queue_len'] != 0:
        while 'running' in r.json and r.json['running']:
            r = requests.get(
                'http://tumblr-conn.appspot.com/ajax/{}/mapping/status'.format(
                    blog_name))
            if r.json()['queue_len'] != 0:
                print('The queue is {} posts long, and we are at the {}th post'.format(
                    r.json['queue_len'], r.json['cur_index']))
                time.sleep(2.5)

    print()
    if float(r.json['endtime']) != 0:
        print('Analysis finalised at %s' % r.json['endtime'])
        print('Analysis took %s seconds' % (
            float(r.json['endtime']) - float(r.json['starttime'])))
        print('The backend considered it a', end=' ')
        print('failure' if r.json['failed'] else 'success')
    else:
        print('Analysis is yet to end')
else:
    print('No previous analysis found')
