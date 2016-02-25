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
import logging.handlers
import os
import sys

def setup_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s.%(funcName)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    myprocess=os.path.basename(sys.argv[0])
    myprocessName=os.path.splitext(myprocess)[0]
    if "OCPMON_DONTSYSLOG" not in os.environ:
        syslogger = logging.handlers.SysLogHandler(address='/dev/log')  
        syslogger.setLevel(logging.INFO)
        sys_formatter = logging.Formatter(fmt=myprocessName+'[%(process)d]: %(module)s: %(levelname)s - %(message)s')
        syslogger.setFormatter(sys_formatter)
        logger.addHandler(syslogger)

    return logger
