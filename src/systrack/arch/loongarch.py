from typing import Tuple, List, Optional

from ..elf import ELF, E_MACHINE, E_FLAGS
from ..kconfig_options import VERSION_INF
from ..type_hints import KernelVersion
from ..utils import VersionedDict

from .arch_base import Arch

class ArchLoongArch(Arch):
	name = 'loongarch'
	syscall_num_reg = 'a7'
	syscall_arg_regs = ('a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6')

	kconfig = VersionedDict(
		(
			# kexec_load
			((6, 1), VERSION_INF, 'KEXEC=y', ['MMU=y']),
			# seccomp
			((5, 19), (5, 10), 'SECCOMP=y', []),
			# mbind, {migrate.move}_pages, {get,set}_mempolicy
			((5, 19), VERSION_INF, 'NUMA=y', ['SMP=y']),
		)
	)

	def __init__(self, kernel_version: KernelVersion, abi: str, bits32: bool = False):
		super().__init__(kernel_version, abi, bits32)
		assert kernel_version >= (5, 19), (
			'Mainline Linux only supports LoongArch from v5.19'
		)
		assert self.abi in ('la32', 'la64')

		if self.abi == 'la32':
			self.abi_bits32 = True
			assert self.bits32

		if self.bits32:
			assert kernel_version >= (6, 19), (
				'Mainline Linux only supports 32-bit LoongArch from v6.19'
			)
			self.config_targets = ('loongson32_defconfig',)
		else:
			if kernel_version >= (6, 19):
				self.config_targets = ('loongson64_defconfig',)
			else:
				self.config_targets = ('loongson3_defconfig',)

			# kexec_file_load
			self.kconfig.add((6, 18), VERSION_INF, 'KEXEC_FILE=y', ['64BIT=y'])

	@staticmethod
	def match(vmlinux: ELF) -> Optional[Tuple[bool, List[str]]]:
		if vmlinux.e_machine != E_MACHINE.EM_LOONGARCH:
			return None

		if vmlinux.bits32:
			abis = ['la32']
		else:
			abis = ['la64']

		return vmlinux.bits32, abis

	def matches(self, vmlinux: ELF) -> bool:
		assert not vmlinux.big_endian, 'Big-endian LoongArch kernel? WAT'
		assert ((vmlinux.e_flags & E_FLAGS.EF_LOONGARCH_ABI_MASK) >> 6) == 1, (
			'Unsupported ABI version'
		)
		return (
			vmlinux.e_machine == E_MACHINE.EM_LOONGARCH
			and vmlinux.bits32 == self.bits32
		)
