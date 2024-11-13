# Copyright (c) 2021 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import importlib
import platform
from typing import Optional

from ...isas import ISA
from ...utils.requires import requires
from .base_cpu_core import BaseCPUCore
from .cpu_types import CPUTypes


class SimpleCore(BaseCPUCore):
    """
    A `SimpleCore` instantiates a core based on the CPUType enum pass. The
    `SimpleCore` creates a single `SimObject` of that type.
    """

    # [Shixin] Add kaslr config
    def __init__(
            self, cpu_type: CPUTypes, core_id: int, isa: ISA,
            protect_kaslr: bool = False,
            protect_module_kaslr: bool = False,
            protect_user_aslr: bool = False,
            kaslr_offset: int = 0,
            clear_tlb_roi: bool = False,
            spec_inst_count_step: int = 1000000000,
            spec_inst_warmup_step: int = 10,
    ):
        requires(isa_required=isa)
        super().__init__(
            core=SimpleCore.cpu_simobject_factory(
                isa=isa, cpu_type=cpu_type, core_id=core_id,
                protect_kaslr=protect_kaslr,
                protect_module_kaslr=protect_module_kaslr,
                protect_user_aslr=protect_user_aslr,
                kaslr_offset=kaslr_offset,
                clear_tlb_roi=clear_tlb_roi,
                spec_inst_count_step=spec_inst_count_step,
                spec_inst_warmup_step=spec_inst_warmup_step,
            ),
            isa=isa,
        )

        self._cpu_type = cpu_type

    def get_type(self) -> CPUTypes:
        return self._cpu_type

    @classmethod
    def cpu_class_factory(cls, cpu_type: CPUTypes, isa: ISA) -> type:
        """
        A factory used to return the SimObject type  given the cpu type,
        and ISA target. An exception will be thrown if there is an
        incompatibility.

        :param cpu_type: The target CPU type.
        :param isa: The target ISA.
        """

        assert isa is not None
        requires(isa_required=isa)

        _isa_string_map = {
            ISA.X86: "X86",
            ISA.ARM: "Arm",
            ISA.RISCV: "Riscv",
            ISA.SPARC: "Sparc",
            ISA.POWER: "Power",
            ISA.MIPS: "Mips",
        }

        _cpu_types_string_map = {
            CPUTypes.ATOMIC: "AtomicSimpleCPU",
            CPUTypes.O3: "O3CPU",
            CPUTypes.TIMING: "TimingSimpleCPU",
            CPUTypes.KVM: "KvmCPU",
            CPUTypes.MINOR: "MinorCPU",
            CPUTypes.NONCACHING: "NonCachingSimpleCPU",
        }

        if isa not in _isa_string_map:
            raise NotImplementedError(
                f"ISA '{isa.name}' does not have an"
                "entry in `AbstractCore.cpu_simobject_factory._isa_string_map`"
            )

        if cpu_type not in _cpu_types_string_map:
            raise NotImplementedError(
                f"CPUType '{cpu_type.name}' "
                "does not have an entry in "
                "`AbstractCore.cpu_simobject_factory._cpu_types_string_map`"
            )

        if cpu_type == CPUTypes.KVM:
            # For some reason, the KVM CPU is under "m5.objects" not the
            # "m5.objects.{ISA}CPU".
            module_str = f"m5.objects"
        else:
            module_str = f"m5.objects.{_isa_string_map[isa]}CPU"

        # GEM5 compiles two versions of KVM for ARM depending upon the host CPU
        # : ArmKvmCPU and ArmV8KvmCPU for 32 bit (Armv7l) and 64 bit (Armv8)
        # respectively.

        if (
            isa.name == "ARM"
            and cpu_type == CPUTypes.KVM
            and platform.architecture()[0] == "64bit"
        ):
            cpu_class_str = (
                f"{_isa_string_map[isa]}V8"
                f"{_cpu_types_string_map[cpu_type]}"
            )
        else:
            cpu_class_str = (
                f"{_isa_string_map[isa]}" f"{_cpu_types_string_map[cpu_type]}"
            )

        try:
            to_return_cls = getattr(
                importlib.import_module(module_str), cpu_class_str
            )
        except ImportError:
            raise Exception(
                f"Cannot find CPU type '{cpu_type.name}' for '{isa.name}' "
                "ISA. Please ensure you have compiled the correct version of "
                "gem5."
            )

        return to_return_cls

    @classmethod
    def cpu_simobject_factory(
        cls, cpu_type: CPUTypes, isa: ISA, core_id: int,
            protect_kaslr: bool = False,
            protect_module_kaslr: bool = False,
            protect_user_aslr: bool = False,
            kaslr_offset: int = 0,
            clear_tlb_roi: bool = False,
            spec_inst_count_step: int = 1000000000,
            spec_inst_warmup_step: int = 10,
    ) -> BaseCPUCore:
        """
        A factory used to return the SimObject core object given the cpu type,
        and ISA target. An exception will be thrown if there is an
        incompatibility.

        :param cpu_type: The target CPU type.
        :param isa: The target ISA.
        :param core_id: The id of the core to be returned.
        """

        to_return_cls = cls.cpu_class_factory(cpu_type=cpu_type, isa=isa)

        # [Shixin] Add kaslr config
        from m5.objects.BaseCPU import BaseCPU

        if protect_kaslr:
            print("@@@ In cpu core enable protect_kaslr")
        else:
            print("@@@ In cpu core disable protect_kaslr")

        if protect_module_kaslr:
            print("@@@ In cpu core enable protect_module_kaslr")
        else:
            print("@@@ In cpu core disable protect_module_kaslr")

        if protect_user_aslr:
            print("@@@ In cpu core enable protect_user_aslr")
        else:
            print("@@@ In cpu core disable protect_user_aslr")

        if clear_tlb_roi:
            print("@@@ Clear TLB at ROI")
        else:
            print("@@@ Do not clear TLB at ROI")

        print("@@@ spec_inst_count_step = ", spec_inst_count_step)
        print("@@@ spec_inst_warmup_step = ", spec_inst_warmup_step)

        if issubclass(to_return_cls, BaseCPU):
            return to_return_cls(
                cpu_id=core_id,
                protectKaslr=protect_kaslr,
                protectModuleKaslr=protect_module_kaslr,
                protectUserAslr=protect_user_aslr,
                kaslrOffset=kaslr_offset,
                clearTlbRoi=clear_tlb_roi,
                specInstCountStep=spec_inst_count_step,
                specInstWarmupStep=spec_inst_warmup_step,
            )

        return to_return_cls(
            cpu_id=core_id
        )
