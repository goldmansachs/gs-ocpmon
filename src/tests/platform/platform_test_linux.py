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

import glob
import logging
import os
import re
import json
import types

from nose.tools import (assert_equals, assert_true)
from mock import MagicMock

from gs_ocpmon.platform.linux import Linux as Plat
from gs_ocpmon.utils import misc

logger = logging.getLogger("root")


def test_tmpdir():
    assert_equals("/tmp", Plat.get_tempdir())


def test_get_trapsink():
    test_base = 'tests/platform/linux-get_system_trapsinks-snmpd_conf'
    expected = json.load(open(test_base + '.expect', 'r'))
    result = Plat().get_system_trapsinks(snmpd_conf_file=test_base + '.in')
    assert_equals(expected, result,
                  "Command result did not match expected result: {0} == {1}".format(str(expected)[:60], str(result)[:60]))

    test_base = 'tests/platform/linux-get_system_trapsinks-snmpd_conf-with_port'
    expected = json.load(open(test_base + '.expect', 'r'))
    result = Plat().get_system_trapsinks(snmpd_conf_file=test_base + '.in')
    assert_equals(expected, result,
                  "Command result did not match expected result: {0} == {1}".format(str(expected)[:60], str(result)[:60]))
