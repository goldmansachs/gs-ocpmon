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
import copy

from nose.tools import (assert_equals, assert_true)

from gs_ocpmon.providers.ddcli import Ddcli
from gs_ocpmon.utils import misc
from mock import MagicMock, patch

logger = logging.getLogger("root")


def setup():
    global ddcli_instance
    ddcli_instance = Ddcli()
    global default_stash
    default_stash = ddcli_instance.exe["commands"]["health"]["default_stash"]


def test1():
    global ddcli_instance
    logger.info("commands are: %s" % [c for c in ddcli_instance.exe["commands"]] )


def test_generator():
    for fname in glob.glob('tests/ddcli/ddcli*.in'):
        test_generator.__name__ = str(fname)
        #if fname == "tests/ipmitool-mc_selftest-ok.in": continue
        logger.debug("test input file is: " + fname)
        resultfile = fname.replace(".in", ".expect")
        logger.debug("resultfile is: " + resultfile)
        assert_true(os.path.exists(resultfile), "no matching .expect file for input file")
        testcmd = 'cat {0}'.format(fname)
        mmatch = re.match("tests/ddcli/ddcli-(\S+?)-", str(fname))
        assert_true(mmatch, "couldnt match method name in input filename: {0}".format(fname))
        method = mmatch.group(1)
        logger.debug("matched method name: " + method)
        with open(resultfile, 'r') as rf:
            yield check_em, testcmd, method, json.load(rf)


def tojson(infile):
    with open(infile, 'r') as rf:
        try:
            with open(infile+".json", 'w') as t:
                import json
                exdict = eval(rf.read())
                json.dump(exdict, t, indent=4)
        except:
            pass


def check_em(testcmd, methodname, expected):
    #result = ddcli_instance.runcmd(testcmd)
    method = getattr(ddcli_instance, methodname)
    def new_runcmd(*args, **kwargs):
        return misc.runcmd(testcmd).stdout
    ddcli_instance.runcmd = MagicMock(side_effect=new_runcmd, autospec=True)
    result = method()
    logger.debug("mocked runcmd called with: {0} ".format(str(ddcli_instance.runcmd.call_args)))
    #exdict = eval(expected.read())
    logger.info("expected, result are: {0}, {1}".format(type(expected), type(result)))
    assert_equals(expected, result, "Command result did not match expected result")


def zest_post():
    testcmd = 'cat tests/ddcli-get_health-ok.in'
    def new_runcmd(*args, **kwargs):
        return misc.runcmd(testcmd)
    ddcli_instance.runcmd = MagicMock(side_effect=new_runcmd, autospec=True)
    ddcli_instance.http_post_health()


def test_check_health_threshold_single():
    if os.path.isfile(ddcli_instance.stash_file):
        os.remove(ddcli_instance.stash_file)
    d = copy.copy(default_stash)
    assert_equals(check_health(d), Ddcli.return_codes.NO_CHANGE_IN_HEALTH)
    d["warranty_remaining"] = "90"
    assert_equals(check_health(d, aid=5904), Ddcli.return_codes.INFORMATIONAL)
    d["warranty_remaining"] = "85"
    assert_equals(check_health(d), Ddcli.return_codes.DIDNT_PASS_THRESHOLD)
    d["warranty_remaining"] = "79"
    assert_equals(check_health(d, aid=5904), Ddcli.return_codes.INFORMATIONAL)
    d["warranty_remaining"] = "49"
    assert_equals(check_health(d, aid=5902), Ddcli.return_codes.WARNING)
    d["warranty_remaining"] = "6"
    assert_equals(check_health(d, aid=5900), Ddcli.return_codes.CRITICAL)


def test_check_health_threshold_list():
    if os.path.isfile(ddcli_instance.stash_file):
        os.remove(ddcli_instance.stash_file)
    d = copy.copy(default_stash)
    assert_equals(check_health(d), Ddcli.return_codes.NO_CHANGE_IN_HEALTH)
    d["warranty_remaining"] = "79"
    assert_equals(check_health(d, aid=5904), Ddcli.return_codes.INFORMATIONAL)
    d["lifeleft"] = ["100", "100", "100", "95"]
    assert_equals(check_health(d), Ddcli.return_codes.DIDNT_PASS_THRESHOLD)
    d["lifeleft"] = ["100", "100", "100", "90"]
    assert_equals(check_health(d, aid=5922), Ddcli.return_codes.INFORMATIONAL)
    d["lifeleft"] = ["100", "100", "90", "90"]
    assert_equals(check_health(d), Ddcli.return_codes.NOT_LOWER_LOW)
    d["lifeleft"] = ["100", "100", "90", "49"]
    assert_equals(check_health(d, aid=5920), Ddcli.return_codes.WARNING)
    d["lifeleft"] = ["6", "5", "5", "49"]
    assert_equals(check_health(d, aid=5918), Ddcli.return_codes.CRITICAL)


def test_check_health_overall_health():
    if os.path.isfile(ddcli_instance.stash_file):
        os.remove(ddcli_instance.stash_file)
    d = copy.copy(default_stash)
    assert_equals(check_health(d), Ddcli.return_codes.NO_CHANGE_IN_HEALTH)
    d["overall_health"] = "WARNING"
    assert_equals(check_health(d, aid=5914), Ddcli.return_codes.WARNING)
    d["overall_health"] = "ERROR"
    assert_equals(check_health(d, aid=5916), Ddcli.return_codes.CRITICAL)


def test_check_health_backup_rail():
    if os.path.isfile(ddcli_instance.stash_file):
        os.remove(ddcli_instance.stash_file)
    d = copy.copy(default_stash)
    assert_equals(check_health(d), Ddcli.return_codes.NO_CHANGE_IN_HEALTH)
    d["backup_rail_monitor"] = "WARNING"
    assert_equals(check_health(d, aid=5908), Ddcli.return_codes.WARNING)
    d["backup_rail_monitor"] = "ERROR"
    assert_equals(check_health(d, aid=5910), Ddcli.return_codes.CRITICAL)


def test_check_health_unknown_status():
    d = copy.copy(default_stash)
    d["backup_rail_monitor"] = "WWHHHH"
    assert_equals(check_health(d, aid=9999), Ddcli.return_codes.UNKNOWN_VALUE)


@patch('gs_ocpmon.providers.notifiers.snmptrap.SnmpTrap.notify')
def check_health(thedict, mock_notify, aid=None):
    def new_get_health():
        return thedict
    def new_send_alert(*args,**kwargs):
        logger.info("Notification Endpoints called for: {0} {1}".format(args, kwargs))
        logger.info(args[0])
        logger.info("\n")
        return 0
    ddcli_instance.get_health = MagicMock(side_effect=new_get_health, autospec=True)
    ddcli_instance.send_alert = MagicMock(side_effect=new_send_alert, autospec=True)
    mock_notify.return_value = 0

    rv = ddcli_instance.check_health()

    if mock_notify.called:
        #((cmd,), arg_d) = mock_sendtrap.call_args
        if aid:
            args, kwargs = mock_notify.call_args
            #logger.debug(kwargs["vars_list"])
            assert_true(kwargs["vars_list"][0] == aid)
        if mock_notify.call_args:
            logger.debug("mocked sendtrap called with: {0} ".format(str(mock_notify.call_args)))

    return rv

def zest_check_health():
    testcmd = 'cat tests/ddcli-get_health-warning.in'

    def new_runcmd(*args, **kwargs):
        return misc.runcmd(testcmd)

    ddcli_instance.runcmd = MagicMock(side_effect=new_runcmd, autospec=True)
    ddcli_instance.check_health()
