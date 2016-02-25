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

import logging

import socket
import os
import sys

from gs_ocpmon.utils import misc

logger = logging.getLogger("root")


class ExecHandler(object):
    @staticmethod
    def load_config(configFile):
        try:
            return misc.json_file_to_dict(configFile)
        except IOError as e:
            logger.info("IOError loading Config file : {0}".format(e))
            print "IOError loading Config File"

    @classmethod
    def notify (cls,message, severity, alertgroup=None,alerttype='http',installer=None,category=None, platform='UNIX', division=None, bu=None, vars_list=None):
        '''
        -s severity (0=test/temp,1=auto, 2=ops(warn), 3=ops(minor), 4=ops(major),5=ops(critical)
        '''
        root_module = sys.modules[cls.__module__.split('.')[0]].__file__
        rootdir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(root_module))))
        config_file = rootdir+"/conf/notify.json"
        if os.path.exists(config_file):
            config_dict = cls.load_config(config_file)
            try:
                execFile   = config_dict['notification_endpoints'][cls.__name__]["execFile"]
            except KeyError:
                logger.info("There is no \"execFile\" key in the config file")
        else :
            raise RuntimeError( "No ExecHandlers Configured")

        host = socket. gethostname()
        if vars_list:
            vars_str = ','.join(str(x) for x in vars_list)

        args = "{0} : {1} : {2}".format(host,message,vars_str)
        cmd = execFile+" "+args
        env = None
        try:
            env = dict()
            env['PATH'] = config_dict['notification_endpoints'][cls.__name__]["path"]
            env['LD_LIBRARY_PATH'] = config_dict['notification_endpoints'][cls.__name__]["ldLibraryPath"]

        except KeyError:
            logger.info("There is no \"path\" key in the config file")
            env=None
#        print '=========================='+cmd
        result = misc.runcmd(cmd,env)
#        print '=========================='+ str(result.return_code)
        if result.return_code:
            logger.error("{0}: non-zero exit code [{1}] for command {2}".format(execFile, result.return_code, cmd))
        return result.return_code
