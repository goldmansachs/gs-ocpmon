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
import json

import os
import re
import csv
import sys
import StringIO
import logging

from . import misc

logger = logging.getLogger("root")


class ExeWrapper(object):
    '''
    classdocs
    '''

    def __init__(self, exe_name, cmd_defs=None):
        '''
        Constructor
        '''

        sub_path = sys.modules[self.__module__].__file__
        self.basedir = os.path.dirname(os.path.abspath(sub_path))
        root_module = sys.modules[self.__module__.split('.')[0]].__file__
        self.rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(root_module))))

        if cmd_defs:
            self.exe = cmd_defs
        else:
            self.exe = misc.json_file_to_dict("{0}/conf/{1}_defs.json".format(self.rootdir, exe_name))

        self.stash = dict()

        for alias, cmd in self.exe["commands"].items():
            if cmd["type"] == "ini" and cmd["generate"] == "True":
                logger.debug("generating getter for {0}".format(alias))
                self.generate_getters(str(alias))
            self.stash[alias] = {}

    def generate_getters(self, cmd):
        def innercmd():
            return self.cmd_colon_sep(cmd)
        innercmd.__name__ = "get_{0}".format(cmd)
        setattr(self, innercmd.__name__, innercmd)

    def get_env(self):
        env = dict()  # os.environ.copy()
        cfgpth = self.exe["path"]
        if cfgpth and not os.path.isabs(cfgpth):
            cfgpth = self.rootdir + os.path.sep + cfgpth
        #appending to PATH variable
        path = os.environ['PATH']
        env['PATH'] = cfgpth +":"+ path
        try:
            env['LD_LIBRARY_PATH'] = self.exe["ld_library_path"] +":"+ os.environ['LD_LIBRARY_PATH'] 
        except:
            env['LD_LIBRARY_PATH'] = self.exe["ld_library_path"]
        return env

    def runcmd(self, cmd, args=None):
        subc = self.exe["commands"][cmd]
        if args == 0 or args is not None:
            logger.debug("runcmd got args: " + str(args))
            args = subc["args"] % args
        else:
            args = subc["args"]
        actual_command = self.exe["cmdline"] + " " + args

        result = misc.runcmd(actual_command, env=self.get_env())

        if subc['type'] == 'exitcode':
            if result.return_code:
                logger.error("{0}: non-zero exit code [{1}] for command {2}".format(self.exe["name"], result.return_code, actual_command))
            return result.stdout.rstrip()

        return result

    def cmd_colon_sep(self, cmd, args=None):
        #if cmd in self.stash:
        #    logger.debug("cmd output already in stash - returning that instead")  
        #    return self.stash[cmd]
        outdict = {}
        cmd_def = self.exe["commands"][cmd]
        result = self.runcmd(cmd, args=args)
        patt = re.compile(r"""^\s*(.*?)\s*?: (.*?)$""", re.M)
        for pair in re.findall(patt, result.stdout):
            #logger.debug(pair)
            if pair[0] in cmd_def["fields"].keys():
                # check for duplicate field names
                key = str(cmd_def["fields"][pair[0]])
                i = 1
                while key in outdict:
                    key += "_%d" % i
                    i += 1
                outdict[key] = pair[1]
                #logger.debug("key = %s" % key)
        self.stash[cmd] = outdict
        if not outdict:
            logger.warn("outdict from command {0} is empty".format(cmd))
        else:
            #logger.debug("outdict = ", vars(outdict))
            logger.debug("outdict = {0}".format(outdict))
        return outdict

    def cmd_comma_sep(self, cmd, args=None, dumpfile=None):
        cmd_def = self.exe["commands"][cmd]
        fields = cmd_def["fields"]
        #logger.debug("%s: csv fields are %s" % (cmd, fields))
        result = self.runcmd(cmd, args=args)
        csv_reader = csv.DictReader(StringIO.StringIO(result.stdout), fieldnames=fields)

        #dumpfile = "ipmitool-get_%s-ok.expect" % cmd
        if dumpfile:
            import json
            try:
                out = [obj for obj in csv_reader]
                with open(dumpfile, 'w') as f:
                    json.dump(out, f)
                    # for row in csv_reader:
                    #     f.write(str(row))
                    #     logger.debug(row)
            except csv.Error as e:
                logger.error('Error reading out for {0}: line {1}: {2}'.format(cmd, csv_reader.line_num, e))

        rows = [obj for obj in csv_reader]
        logger.debug("%s: got a row count of %d" % (cmd, len(rows)))
        return rows

    def cmd_json_enc(self, cmd, args=None):
        outdict = {}
        cmd_def = self.exe["commands"][cmd]
        result = self.runcmd(cmd, args=args)
        outdict = json.loads(result.stdout)
        self.stash[cmd] = outdict
        if not outdict:
            logger.warn("outdict from command {0} is empty".format(cmd))
        return outdict
