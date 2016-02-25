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


try:
    import platform
    platsys = platform.system()
    if platsys == "Linux":
        from .linux import Linux as Plat
    elif platsys == "VMkernel":
        from .esx import Esx as Plat
    elif platform.system() == "Windows":
        from .windows import Windows as Plat
    else:
        raise RuntimeError("Platform detection failed for %s" % platsys)
except ImportError as ie:
    # ESXi 2.6 is missing 'platform' system library - use os
    import os
    if os.uname() and os.uname()[0] == "VMkernel":
        from .esx import Esx as Plat
    else:
        raise RuntimeError("Platform detection failed")
