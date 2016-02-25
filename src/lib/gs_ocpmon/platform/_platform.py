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
from __future__ import absolute_import

import abc
import tempfile


class Base(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_system_trapsinks(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_baseboard_manufacturer(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_baseboard_product_name(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_baseboard_version(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_chassis_asset_tag(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_chassis_serial_number(self):
        raise NotImplementedError

    @staticmethod
    def get_tempdir():
        return tempfile.gettempdir()
