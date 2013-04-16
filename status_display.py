import sys
import requests
import time

argv = sys.argv[1:]
blog_name = argv[0] if len(argv) > 0 else 'mause-me'


print('Tracing the blog "%s"\n'.format(blog_name))

r = requests.get(
    'http://tumblr-conn.appspot.com/ajax/%s/mapping/status' % blog_name)

if r.json['queue'] == []:
    print('Post queue is empty.')

if not r.json['running']:
    print('Not running. Displaying statistics from last analysis.\n')


if float(r.json['starttime']) != 0:
    print('Analysis began at %s' % r.json['starttime'])

    if r.json['queue'] != []:
        while 'running' in r.json and r.json['running']:
            r = requests.get(
                'http://tumblr-conn.appspot.com/ajax/{}/mapping/status'.format(
                    blog_name))
            if r.json['queue'] != []:
                print('The queue is {} posts long, and we are at the {}th post'.format(
                    len(r.json['queue']), r.json['cur_index']))
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
