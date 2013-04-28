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
"url manipulation and verification"

# stdlib
import json
import logging
import urllib.parse


# countries.json from https://raw.github.com/mledoze/countries/master/countries.json
with open('countries.json') as fh:
    COUNTRIES = json.load(fh)
    TLDS = {country['tld'] for country in COUNTRIES}


def is_url(string):
    if string.split('://')[0] not in ['http', 'https']:
        string = 'http://' + string

    netloc = urllib.parse.urlsplit(string).netloc
    # logging.debug('netloc; "{}"'.format(netloc))
    if netloc.split('.')[-1] in TLDS:
        # eh, good enough
        return True
    else:
        return False


def expand_hostname(hostname):
    # logging.debug('Expanding hostname; "{}"'.format(hostname))
    if hostname.endswith('.tumblr.com'):
        return

    if not is_url(hostname):
        # if it appears to be invalid, format as tumblr url
        return '{}.tumblr.com'.format(hostname)
    else:
        return hostname


def build_url(hostname):
    hostname = expand_hostname(hostname)
    return 'http://api.tumblr.com/v2/blog/{}.tumblr.com/'.format(hostname)


def main():
    logging.info = print
    while True:
        print(is_url(input('URL; ')))
        # print(expand_hostname(input()))

if __name__ == '__main__':
    main()
