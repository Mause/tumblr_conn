"graph representation generators"
import json
import logging
from utils import memcache
from itertools import chain


def process_graph_data(handler, processing_function):
    blog_name = handler.get_argument('blog_name')
    output_json = {'nodes': [], 'links': []}

    if blog_name:
        sink, source = [], []
        sink = memcache.get(blog_name + '_sink') or {}
        source = memcache.get(blog_name + '_source') or {}

        # looks messy, but just combines the dicts into one big dict
        # and grabs the values
        all_data = source
        all_data.update(sink)
        all_data = all_data.values()

        if all_data:
            # yay for (memory efficient) generators \o/

            # ensure we are dealing with data!
            all_data = filter(bool, all_data)

            # flatten that data!
            all_data = chain.from_iterable(all_data)

            # ensure we are dealing with non-duplicated data!
            all_data = set(all_data)

            output_json = processing_function(all_data)

    return json.dumps(
        output_json)


def compute_d3_points(relations):
    output_json = {'links': [], 'nodes': []}
    if relations:
        unique = set(chain.from_iterable(relations))

        id_relations = {}
        for cur_id, frag in enumerate(unique):
            id_relations[frag] = cur_id

        for rel in unique:
            output_json['nodes'].append(
                {
                    'blog_name': rel,
                    'blog_id': id_relations[rel],
                    'weight': 5
                })

        for rel in relations:
            output_json['links'].append(
                {
                    'source': id_relations[rel[0]],
                    'target': id_relations[rel[1]],
                    'weight': 5
                })

        logging.info('Posts; {}'.format(len(output_json['nodes'])))
        logging.info('Post links; {}'.format(len(output_json['links'])))

    return output_json


def compute_radial_d3_points(relations):
    """formats a list of tuples to a format displayable
    on the radial type d3 graph"""
    if relations:
        id_relations = {}
        unique = set(chain.from_iterable(relations))

        for frag in unique:
            id_relations[frag] = {
                "name": frag,
                "imports": []}

        for rel in relations:
            id_relations[rel[0]]['imports'].append(rel[1])

        logging.info('Posts; {}'.format(len(id_relations)))

        return list(id_relations.values())
    else:
        return []


def main():
    # from pprint import pprint

    input_data = list(zip(range(100), range(101, 200)))
    input_data += list(zip(range(100), range(101, 200)))
    input_data = input_data
    # pprint(input_data)
    output = compute_d3_points(input_data)
    print(json.dumps(output, indent=4))
    # pprint(output)


if __name__ == '__main__':
    main()
