#!/bin/env python
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

from .ddcli import Ddcli
from gs_ocpmon.utils import misc
import os
ddcli = Ddcli()
thedict, thetsv = ddcli.gen_alert_table()

basedir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.dirname(basedir)
misc.dict_to_json_file(thedict,parentdir+"/conf/ddcli_alert_map.json")

with open("ddcli_alert_ids.tsv", "wb") as csv:
    csv.write(thetsv)
