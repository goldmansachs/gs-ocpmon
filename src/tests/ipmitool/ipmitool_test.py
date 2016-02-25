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
from mock import MagicMock, patch

import gs_ocpmon

from gs_ocpmon.providers.ipmitool import Ipmitool
from gs_ocpmon.utils import misc

logger = logging.getLogger("root")

def setup():

    #logger.info("In setup")
    # stub sdr_dump out
    Ipmitool.sdr_dump = lambda *s: 0
    #patch('gs_ocpmon.platform.Plat.get_baseboard_product_name').start().return_value = 'DCS 1240'
    patch('gs_ocpmon.platform.Plat.get_baseboard_product_name').start().return_value = 'D51B-1U (dual 1G LoM)'


def test_show_commands():
    for k in Ipmitool().exe["commands"].keys():
        logger.info("ipmitool commands are: {0}".format(k))


#def test_sdr_loc_esx():
#    sdr_loc = Ipmitool().get_sdr_location()
#    assert_equals("/var/tmp/D51B.sdr.dump", sdr_loc, "Ipmitool.get_sdr_location " + sdr_loc)


def test_generator():
    for fname in glob.glob('tests/ipmitool/ipmitool*.in'):
        test_generator.__name__ = str(fname)
        #if fname == "tests/ipmitool-mc_selftest-ok.in": continue
        logger.debug("test input file is: " + fname)
        resultfile = fname.replace(".in", ".expect")
        logger.debug("resultfile is: " + resultfile)
        assert_true(os.path.exists(resultfile), "no matching .expect file for input file")
        testcmd = 'cat {0}'.format(fname)
        mmatch = re.match("tests/ipmitool/ipmitool-(\S+?)-", str(fname))
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
    result = mockery(Ipmitool(), methodname, testcmd)()

    #logger.debug("expected, result are: %s, %s" % (type(expected), type(result)))
    #logger.debug("asserting equals:\n\texpected: %s\n\tresult:   %s" % (expected, result))
    assert_equals(expected, result, "Command result did not match expected result")


def copy_func(f, name=None):
    return types.FunctionType(f.func_code, f.func_globals, name or f.func_name, f.func_defaults, f.func_closure)


def mockery(cls_instance, func, testcmd):
    old_method = getattr(cls_instance, func)

    def new_method(*real_args, **real_kwargs):

        def new_runcmd(*rcargs, **rckwargs):
            if real_args and '%' in testcmd:
                thearg = testcmd % real_args
            else:
                thearg = testcmd
            return misc.runcmd(thearg)
        cls_instance.runcmd = MagicMock(side_effect=new_runcmd, autospec=True)

        result = old_method(*real_args, **real_kwargs)

        ((cmd_name,), arg_d) = cls_instance.runcmd.call_args
        actual = cls_instance.exe["cmdline"]
        cmd = cls_instance.exe["commands"][cmd_name]
        args = arg_d["args"]

        if args == 0 or args is not None:
            logger.debug("runcmd got args: " + str(args))
            args = cmd["args"] % args
        else:
            args = cmd["args"]

        actual += " " + args
        logger.debug("mocked runcmd called with: {0} ".format(actual))

        return result

    return MagicMock(side_effect=new_method, autospec=True)


def zest_event_corpus():
    #for fname in glob.glob('tests/ipmitool/_ipmitool-sel_list_csv-D*.in'):
    for fname in glob.glob('tests/ipmitool/*d51*.in'):
        test_generator.__name__ = str(fname)
        logger.debug("test input file is: " + fname)
        yield check_alerts, fname


# @patch('gs_ocpmon.ipmitool.Utils')
def check_alerts(fname): # , mock_utils):
    cls_instance = Ipmitool()
    logger.debug("Running test_alerts()")
    testcmd = 'cat {0}'.format(fname)

    cls_instance.get_sel_info = mockery(cls_instance, "get_sel_info", 'cat tests/ipmitool/ipmitool-get_sel_info-ok.in')
    # reqd for last_seen_fru
    cls_instance.read_fru_stash = mockery(cls_instance, "read_fru_stash", 'cat tests/ipmitool/_fru_print_0.in')
    # reqd for last_seen_sel
    cls_instance.get_sel_list_csv = mockery(cls_instance, "get_sel_list_csv", testcmd)
    cls_instance.get_sel_list_csv_last = mockery(cls_instance, "get_sel_list_csv_last", testcmd)

    rf = open('%s.result' % fname, 'wb')
    cls_instance.notify_map={"notify": []}
    #mock_utils.sendtrap.return_value = 0

    cls_instance.check_sel()


# def test_read_fru_stash():
#     ret = Ipmitool().read_fru_stash(testcmd="cat tests/ipmitool/ipmitool-get_fru_print-ok.in")
#     logger.info(ret)


def test_post_error_check():
    for fname in glob.glob('tests/ipmitool/_ipmitool_post_error*.in'):
        if "_get_" in str(fname): 
            continue
        test_generator.__name__ = str(fname)
        logger.debug("test input file is: " + fname)
        yield post_error_check, fname


def post_error_check(fname):
    cls_instance = Ipmitool()
    testcmd = 'cat {0}'.format(fname)
    cls_instance.get_sel_list_csv = mockery(cls_instance, "get_sel_list_csv", testcmd)
    test_sel_get_cmd = testcmd.replace(".in", "-sel_get_%s.in")
    cls_instance.get_sel_get = mockery(cls_instance, "get_sel_get", test_sel_get_cmd)
    cls_instance.notify_map={"notify": []}

    cls_instance.post_error_check()


def test_ecc_errors():
    for fname in glob.glob('tests/ipmitool/_ipmitool-ecc-errors.in'):
        if "_get_" in str(fname):  
            continue
        test_generator.__name__ = str(fname)
        logger.debug("test input file is: " + fname)
        yield ecc_error_check, fname


def ecc_error_check(fname):

    cls_instance = Ipmitool()
    logger.debug("Running test_alerts()")
    testcmd = 'cat {0}'.format(fname)

    cls_instance.get_sel_info = mockery(cls_instance, "get_sel_info", 'cat tests/ipmitool/ipmitool-get_sel_info-ok.in')
    # reqd for last_seen_fru
    cls_instance.read_fru_stash = mockery(cls_instance, "read_fru_stash", 'cat tests/ipmitool/_fru_print_0.in')
    # reqd for last_seen_sel
    cls_instance.get_sel_list_csv = mockery(cls_instance, "get_sel_list_csv", testcmd)
    cls_instance.get_sel_list_csv_last = mockery(cls_instance, "get_sel_list_csv_last", testcmd)

    # SEL GET SEL
    test_sel_get_cmd = testcmd.replace(".in", "-sel_get_99.in")
    cls_instance.get_sel_get = mockery(cls_instance, "get_sel_get", test_sel_get_cmd)
    cls_instance.notify_map={"notify": []}
    #mock_utils.sendtrap.return_value = 0

    cls_instance.check_sel()
