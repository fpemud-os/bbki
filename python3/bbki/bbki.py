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


import os
import glob
import robust_layer.simple_fops
from .util import Util
from .fs_layout import FsLayoutLinux
from .repo import Repo
from .repo import BbkiFileExecutor
from .boot_entry import BootEntry
from .boot_entry import BootEntryUtils
from .kernel import KernelInstaller
from .initramfs import InitramfsInstaller
from .bootloader import BootLoaderGrub


class Bbki:

    KERNEL_TYPE_LINUX = "linux"

    SYSTEM_INIT_SYSVINIT = "sysv-init"
    SYSTEM_INIT_OPENRC = "openrc"
    SYSTEM_INIT_SYSTEMD = "systemd"
    SYSTEM_INIT_CUSTOM = "custom"

    BOOT_MODE_EFI = "efi"
    BOOT_MODE_BIOS = "bios"

    ATOM_TYPE_KERNEL = 1
    ATOM_TYPE_KERNEL_ADDON = 2

    def __init__(self, target_host_info, target_host_is_myself=True, cfg=None):
        self._targetHostInfo = target_host_info
        self._bForSelf = target_host_is_myself
        self._cfg = cfg

        if self._cfg.get_kernel_type() == self.KERNEL_TYPE_LINUX:
            self._fsLayout = FsLayoutLinux(self)
        else:
            assert False

        self._repoList = [
            Repo(self._cfg.data_repo_dir),
        ]

    @property
    def config(self):
        return self._cfg

    @property
    def repositories(self):
        return self._repoList

    @property
    def rescue_os_spec(self):
        return RescueOsSpec(self)

    def check_running_environment(self):
        if not os.path.isdir(self._fsLayout.get_boot_dir()):
            raise RunningEnvironmentError("directory \"%s\" does not exist" % (self._fsLayout.get_boot_dir()))
        if not os.path.isdir(self._fsLayout.get_lib_dir()):
            raise RunningEnvironmentError("directory \"%s\" does not exist" % (self._fsLayout.get_lib_dir()))

        if not Util.cmdCallTestSuccess("sed", "--version"):
            raise RunningEnvironmentError("executable \"sed\" does not exist")
        if not Util.cmdCallTestSuccess("make", "-V"):
            raise RunningEnvironmentError("executable \"make\" does not exist")
        if not Util.cmdCallTestSuccess("grub-install", "-V"):
            raise RunningEnvironmentError("executable \"grub-install\" does not exist")

    def get_current_boot_entry(self):
        if not self._bForSelf:
            return None

        for bHistoryEntry in [False, True]:
            ret = BootEntry.new_from_verstr(self._bbki, "native", os.uname().release, history_entry=bHistoryEntry)
            if ret.has_kernel_files() and ret.has_initrd_files():
                return ret
        return None

    def get_pending_boot_entry(self, strict=True):
        ret = BootLoaderGrub(self).getMainBootEntry()
        if ret is not None and (not strict or (ret.has_kernel_files() and ret.has_initrd_files())):
            return ret
        else:
            return None

    def has_rescue_os(self):
        return os.path.exists(self._fsLayout.get_boot_rescue_os_dir())

    def get_kernel_atom(self):
        items = self._repoList[0].get_items_by_type_name(self.ATOM_TYPE_KERNEL, self._cfg.get_kernel_type())
        items = [x for x in items if self._cfg.check_version_mask(x.fullname, x.verstr)]                    # filter by bbki-config
        if len(items) > 0:
            return items[-1]
        else:
            return None

    def get_kernel_addon_atoms(self):
        ret = []
        for name in self._cfg.get_kernel_addon_names():
            items = self._repoList[0].get_items_by_type_name(self.ATOM_TYPE_KERNEL_ADDON, name)
            items = [x for x in items if self._cfg.check_version_mask(x.fullname, x.verstr)]                # filter by bbki-config
            if len(items) > 0:
                ret.append(items[-1])
        return ret

    def fetch(self, atom):
        BbkiFileExecutor(atom).exec_fetch()

    def get_kernel_installer(self, kernel_atom, kernel_addon_atom_list):
        assert kernel_atom.atom_type == self.ATOM_TYPE_KERNEL
        assert all([x.atom_type == self.ATOM_TYPE_KERNEL_ADDON for x in kernel_addon_atom_list])

        return KernelInstaller(self, kernel_atom, kernel_addon_atom_list)

    def install_initramfs(self, boot_entry):
        if self._targetHostInfo.boot_disk is None:
            raise RunningEnvironmentError("no boot/root device specified")

        InitramfsInstaller(self, boot_entry).install()

    def install_bootloader(self):
        if self._targetHostInfo.boot_disk is None:
            raise RunningEnvironmentError("no boot/root device specified")

        BootLoaderGrub(self).install()

    def reinstall_bootloader(self):
        if self._targetHostInfo.boot_disk is None:
            raise RunningEnvironmentError("no boot/root device specified")

        obj = BootLoaderGrub(self)
        obj.remove()
        obj.install()

    def update_bootloader(self):
        if self._targetHostInfo.boot_disk is None:
            raise RunningEnvironmentError("no boot/root device specified")

        BootLoaderGrub(self).update()

    def check(self, autofix=False):
        assert False

    def clean_boot_entries(self, pretend=False):
        currentBe = self.get_current_boot_entry()
        pendingBe = self.get_pending_boot_entry()

        # get to-be-deleted files in /boot
        bootFileList = None
        if True:
            tset = set(glob.glob(os.path.join(self._bbki._fsLayout.get_boot_dir(), "*")))                       # mark /boot/* (no recursion) as to-be-deleted
            tset.discard(self._bbki._fsLayout.get_boot_grub_dir())                                              # don't delete /boot/grub
            if self._targetHostInfo.boot_mode == self.BOOT_MODE_EFI:
                tset.discard(self._bbki._fsLayout.get_boot_grub_efi_dir())                                      # don't delete /boot/EFI
            elif self._targetHostInfo.boot_mode == self.BOOT_MODE_BIOS:
                pass
            else:
                assert False
            tset.discard(self._bbki._fsLayout.get_boot_rescue_os_dir())                                         # don't delete /boot/rescue
            if currentBe is not None:
                if currentBe.is_historical():
                    tset.discard(self._bbki._fsLayout.get_boot_history_dir())                                   # don't delete /boot/history since some files in it are referenced
                    tset |= set(glob.glob(os.path.join(self._bbki._fsLayout.get_boot_history_dir(), "*")))      # mark /boot/history/* (no recursion) as to-be-deleted
                    tset -= set(BootEntryUtils(self._bbki).getBootEntryFilePathList(currentBe))                 # don't delete files of current-boot-entry
                else:
                    assert currentBe == pendingBe
            if pendingBe is not None:
                tset -= set(BootEntryUtils(self._bbki).getBootEntryFilePathList(pendingBe))                     # don't delete files of pending-boot-entry
            bootFileList = sorted(list(tset))

        # get to-be-deleted files in /lib/modules
        modulesFileList = []
        if os.path.exists(self._bbki._fsLayout.get_kernel_modules_dir()):
            tset = set(glob.glob(os.path.join(self._bbki._fsLayout.get_kernel_modules_dir(), "*")))             # mark /lib/modules/* (no recursion) as to-be-deleted
            if currentBe is not None:
                tset.discard(currentBe.kernel_modules_dirpath)                                                  # don't delete files of current-boot-entry
            if pendingBe is not None:
                tset.discard(pendingBe.kernel_modules_dirpath)                                                  # don't delete files of pending-boot-entry
            if len(tset) == 0:
                tset.add(self._bbki._fsLayout.get_kernel_modules_dir())                                         # delete /lib/modules since it is empty
            modulesFileList = sorted(list(tset))

        # get to-be-deleted files in /lib/firmware
        firmwareFileList = []                                                                                   # FIXME
        if os.path.exists(self._bbki._fsLayout.get_firmware_dir()):
            if os.listdir(self._bbki._fsLayout.get_firmware_dir()) == []:
                firmwareFileList.append(self._bbki._fsLayout.get_firmware_dir())                                # delete /lib/firmware since it is empty

        # delete files
        if not pretend:
            for fullfn in bootFileList:
                robust_layer.simple_fops.rm(fullfn)
            for fullfn in modulesFileList:
                robust_layer.simple_fops.rm(fullfn)
            for fullfn in firmwareFileList:
                robust_layer.simple_fops.rm(fullfn)

        # return value
        return (bootFileList, modulesFileList, firmwareFileList)

    def clean_distfiles(self, pretend=False):
        return []                               # FIXME

    def remove_all(self):
        # remove boot-loader (may change harddisk MBR)
        if self._targetHostInfo.boot_disk is not None:
            BootLoaderGrub(self).remove()                                               

        Util.removeDirContent(self._bbki._fsLayout.get_boot_dir())                      # remove /boot/*
        robust_layer.simple_fops.rm(self._bbki._fsLayout.get_firmware_dir())            # remove /lib/firmware
        robust_layer.simple_fops.rm(self._bbki._fsLayout.get_kernel_modules_dir())      # remove /lib/modules


class SystemInitInfo:

    def __init__(self, name, init_cmd):
        assert name in [Bbki.SYSTEM_INIT_SYSVINIT, Bbki.SYSTEM_INIT_OPENRC, Bbki.SYSTEM_INIT_SYSTEMD, Bbki.SYSTEM_INIT_CUSTOM]
        self.name = name
        self.init_cmd = init_cmd


class RescueOsSpec:

    def __init__(self, bbki):
        self.root_dir = bbki.fsLayout.get_rescue_os_dir()
        self.kernel_filepath = bbki.fsLayout.get_boot_rescue_os_kernel_filepath()
        self.initrd_filepath = bbki.fsLayout.get_boot_rescue_os_initrd_filepath()


class RunningEnvironmentError(Exception):
    pass


class ConfigError(Exception):
    pass


class RepoError(Exception):
    pass


class FetchError(Exception):
    pass


class KernelInstallError(Exception):
    pass


class InitramfsInstallError(Exception):
    pass


class BootloaderInstallError(Exception):
    pass
