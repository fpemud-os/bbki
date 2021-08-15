#!/usr/bin/env python3

# Copyright (c) 2005-2014 Fpemud <fpemud@sina.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
bbki

@author: Fpemud
@license: GPLv3 License
@contact: fpemud@sina.com
"""

__author__ = "fpemud@sina.com (Fpemud)"
__version__ = "0.0.1"


from .bbki import Bbki
from .bbki import SystemInitInfo
from .bbki import RescueOsSpec

from .host_info import HostInfo
from .host_info import HostMountPoint
from .host_info import HostDisk
from .host_info import HostDiskLvmLv
from .host_info import HostDiskBcache
from .host_info import HostDiskScsiDisk
from .host_info import HostDiskNvmeDisk
from .host_info import HostDiskXenDisk
from .host_info import HostDiskVirtioDisk
from .host_info import HostDiskPartition
from .host_info import HostAuxOs

from .config import Config
from .config import EtcDirConfig

from .repo import Repo
from .repo import RepoAtom

from .boot_entry import BootEntry

from .kernel import KernelInstaller

from .exception import RunningEnvironmentError
from .exception import ConfigError
from .exception import RepoError
from .exception import FetchError
from .exception import KernelInstallError
from .exception import InitramfsInstallError
from .exception import BootloaderInstallError
