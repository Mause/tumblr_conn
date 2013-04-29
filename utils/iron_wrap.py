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
"IronIO API wrappers"

# stdlib
import json

# third party
from ironio import iron_mq
from ironio import iron_cache


# IronCache
class MemcacheContainer(object):
    "provides caches' on demand"
    caches = {}

    def __getitem__(self, cache_name):
        if cache_name not in self.caches:
            self.caches[cache_name] = iron_cache.IronCache()
        return self.caches[cache_name]
memcache = MemcacheContainer()


class Message(object):
    """
    convinence wrapper around a message from a Taskqueue

    automatically decodes json messages and provides a delete method,
    whilst maintaining the dictionary interface"""

    def __init__(self, queue_obj, message):
        self.queue_obj = queue_obj
        self.messages = message['messages']
        for i, m in enumerate(self.messages):
            try:
                self.messages[i]['body'] = json.loads(m['body'])
            except (TypeError, ValueError):
                # if it aint json, leave as is
                pass

    def __getitem__(self, name):
        assert type(self.messages[0]['body']) == dict, self.messages[0]

        return self.messages[0]['body'].__getitem__(name)

    def delete(self):
        "delete contained messages"
        for message in self.messages:
            self.queue_obj.delete(message['id'])

    def __repr__(self):
        content = self.messages[0]['body'] if not self.empty() else []
        return '<Message {}>'.format(content)


# IronMQ
class Taskqueue(object):
    "simple wrapper around IronMQ"
    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.queue = iron_mq.IronMQ(queue_name)

    def get(self):
        messages = self.queue.get()
        if messages['messages']:
            return Message(self.queue, messages)
        else:
            return

    def add(self, params):
        params = json.dumps(params)
        return self.queue.put(params)


class TaskqueueContainer(object):
    """
    wrapper around Taskqueue

    use as if it were a dictionary to access Taskqueue instances"""
    queues = {}

    def __getitem__(self, queue_name):
        if queue_name not in self.queues:
            self.queues[queue_name] = Taskqueue(queue_name)
        return self.queues[queue_name]
taskqueue = TaskqueueContainer()
