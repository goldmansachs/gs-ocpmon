# (C) Copyright 2016, Goldman Sachs. All rights reserved.
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
from __future__ import print_function

from collections import namedtuple
import logging
import re
import shlex
import os
import json
import subprocess as sub

logger = logging.getLogger("root")

__all__ = [
    'runcmd',
    'json_file_to_dict',
    'dict_to_json_file',
    'to_camel_text',
    'get_key_for_nearest_match',
    'get_equivalent_key_with_config'
]


Result = namedtuple("Result", "stdout stderr return_code")


def runcmd(cmd, env=None):
    if env:
        from pprint import pformat
        logger.debug("running {0} with env = {1}".format(cmd, pformat(env)))
    logger.info("running {0}".format(cmd))
    shlex_cmd = shlex.split(cmd.encode('utf-8'))
    cmd = sub.Popen(shlex_cmd, stdout=sub.PIPE, stderr=sub.PIPE, env=env)

    (cmd_out, cmd_err) = cmd.communicate()

    result = Result(cmd_out, cmd_err, cmd.returncode)

    logger.debug("return code: %d" % cmd.returncode)
    return result


def dict_to_json_file(thedict, filename):
    with open(filename, 'wb') as f:
        print(json.dumps(thedict, sort_keys=True, indent=2), file=f)

def dict_to_json(thedict):
    return json.dumps(thedict)

def json_file_to_dict(filename):
    with open(filename, 'rb') as f:
        return json.load(f)

def get_key_for_nearest_match(product, product_map_keys):
    if product in product_map_keys:
        return product
    product_map_keys_sorted=sorted(product_map_keys,
                                  key=lambda x: -1*len(x.replace("*","")))
    for key in product_map_keys_sorted:
        #convert * notion into python .*notation
        re_key=key.replace("*",".*")
        if re.match(re_key,product):
            return key
    return None


def get_equivalent_key_with_config(product_name,product_name_key,product_map):
    if product_name_key == None:
        logger.info("There is no related \"{0}\" key in the config file to ".format(product_name))
        raise RuntimeError( "No Configurations set for the product : {0}".format(product_name))
        return None
    product_name_value = product_map[product_name_key]
    while type(product_name_value) is not dict :
        if product_name_value in product_map.keys():
            product_name_key = product_name_value
            product_name_value = product_map[product_name_key]
        else :
            logger.info("There is no related \"{0}\" key in the config file to ".format(product_name))
            raise RuntimeError( "No Configurations set for the product : {0}".format(product_name))

    return product_name_key


def to_camel_text(text):
    text = text.title()
    text = re.sub('[ -/:_]', '', text)
    text = text[:1].lower() + text[1:]
    return text

def enum(**enums):
    return type('Enum', (), enums)
