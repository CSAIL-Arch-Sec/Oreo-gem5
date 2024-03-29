/*
 * Copyright (c) 2011-2013, 2017, 2020 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2002-2005 The Regents of The University of Michigan
 * Copyright (c) 2011 Regents of the University of California
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __CPU_BASE_HH__
#define __CPU_BASE_HH__

#include <vector>

#include "arch/generic/interrupts.hh"
#include "arch/generic/pcstate.hh"
#include "arch/x86/pcstate.hh"
#include "base/statistics.hh"
#include "debug/Mwait.hh"
#include "mem/htm.hh"
#include "mem/port_proxy.hh"
#include "sim/clocked_object.hh"
#include "sim/eventq.hh"
#include "sim/full_system.hh"
#include "sim/insttracer.hh"
#include "sim/probe/pmu.hh"
#include "sim/probe/probe.hh"
#include "sim/system.hh"

namespace gem5
{

class BaseCPU;
struct BaseCPUParams;
class CheckerCPU;
class ThreadContext;

struct AddressMonitor
{
    AddressMonitor();
    bool doMonitor(PacketPtr pkt);

    bool armed;
    Addr vAddr;
    Addr pAddr;
    uint64_t val;
    bool waiting;   // 0=normal, 1=mwaiting
    bool gotWakeup;
};

class CPUProgressEvent : public Event
{
  protected:
    Tick _interval;
    Counter lastNumInst;
    BaseCPU *cpu;
    bool _repeatEvent;

  public:
    CPUProgressEvent(BaseCPU *_cpu, Tick ival = 0);

    void process();

    void interval(Tick ival) { _interval = ival; }
    Tick interval() { return _interval; }

    void repeatEvent(bool repeat) { _repeatEvent = repeat; }

    virtual const char *description() const;
};

class BaseCPU : public ClockedObject
{
    // [Shixin] Protect KASLR
    Addr getMaxMask(Addr max) {
        // size should be larger than 0
        Addr x = -1;
        for (size_t i = 0; i < 64; i++) {
            if (x >> 1 >= max) {
                x = x >> 1;
            } else {
                return x;
            }
        }
        return x;
    }

public:
    enum KaslrRegionType : size_t
    {
        KaslrKernelRegion = 0,
        KaslrModuleRegion = 1,
        AslrUserRegion = 2,
        NumKaslrRegionType = 3
    };

    bool protectKaslr[NumKaslrRegionType];
    Addr regionStart[NumKaslrRegionType] = {0xffffff8000000000, 0xffffff8000000000, 0};
    Addr regionSize[NumKaslrRegionType] = {0x6000000000, 0x6000000000, 0x20000000000000};
    Addr regionAlignBits[NumKaslrRegionType] = {31, 31, 48};
    Addr regionMask[NumKaslrRegionType] = {0, 0, 0};

    // TODO: In the final design, we should not set kaslrOffset here.
    //  It should be read from page table / TLB during address translation.
    // TODO: In the final design, we should also consider different region
    //  when apply mask and offset
    Addr kaslrOffset;

    bool isKaslrMaskedAddr(Addr addr, size_t region) const {
        return protectKaslr[region] &&
               addr >= regionStart[region] &&
               addr < regionStart[region] + (1 << regionAlignBits[region]);
    }

    bool isKaslrRegionAddr(Addr addr, size_t region) const {
        return protectKaslr[region] &&
               addr >= regionStart[region] &&
               addr < regionStart[region] + regionSize[region];
    }

    Addr getKaslrDeltaFromPC(Addr corrAddr) const {
        for (size_t i = 0; i < NumKaslrRegionType; i++) {
            if (isKaslrRegionAddr(corrAddr, i)) {
                return (corrAddr & (~regionMask[i])) >> regionAlignBits[i];
            }
        }
        return 0;
    }

    void protectKaslrTestMask(const PCStateBase &origPC, bool testDelta, char *note) {
        auto &pc = origPC.as<X86ISA::PCState>();
        if (!protectKaslrValid(pc.pc(), 0) || !protectKaslrValid(pc.npc(), 0)) {
            std::clog << "@@@ Tick " << curTick() << " warn pc/npc protectKaslrTestMask PC State " << pc << " " << note << std::endl;
            warn("@@@ PC/NPC should be masked but not\n");
        }
        if (testDelta && (pc.kaslrCorrDelta() || pc.kaslrNpcDelta())) {
            std::clog << "@@@ Tick " << curTick() << " warn delta protectKaslrTestMask PC State " << pc << " " << note << std::endl;
            warn("@@@ PC/NPC delta should be 0 but not\n");
        }
    }

    void protectKaslrClearDelta(PCStateBase &origPC, bool clearPCDelta, bool clearNPCDelta, char *note) {
        // This function would change origPC
        auto &pc = origPC.as<X86ISA::PCState>();
        if (clearPCDelta) {
            pc.kaslrCorrDelta(0);
        }
        if (clearNPCDelta) {
            pc.kaslrNpcDelta(0);
        }
        protectKaslrTestMask(origPC, false, note);
    }

    void protectKaslrExtractDeltaMask(PCStateBase &origPC) {
        // This function would change origPC
        auto &pc = origPC.as<X86ISA::PCState>();
        auto npcAddr = pc.npc();
        auto newNPCDelta = getKaslrDeltaFromPC(npcAddr);
        // Record NPC delta (which might be freshly set by Wrip)
        pc.kaslrNpcDelta(newNPCDelta);
        // Apply mask to NPC
        pc.npc(protectKaslrMask(npcAddr));
    }

    void protectKaslrApplyNPCCorrDelta(PCStateBase &origPC) {
        // This function would change origPC
        auto &pc = origPC.as<X86ISA::PCState>();
        pc.npc(protectKaslrApplyDelta(pc.npc(), pc.kaslrCorrDelta()));
    }

    void protectKaslrApplyPCCorrDelta(PCStateBase &origPC) {
        // This function would change origPC
        auto &pc = origPC.as<X86ISA::PCState>();
        pc.pc(protectKaslrApplyDelta(pc.pc(), pc.kaslrCorrDelta()));
    }

    Addr protectKaslrMask(Addr addr) {
        // This function only apply mask to address in KASLR randomization
        //   region when protect KASLR is enabled.
        for (size_t i = 0; i < NumKaslrRegionType; i++) {
            if (isKaslrRegionAddr(addr, i)) {
                return addr & regionMask[i];
            }
        }
        return addr;
    }

    Addr protectKaslrApplyDelta(Addr addr, Addr delta) {
        for (size_t i = 0; i < NumKaslrRegionType; i++) {
            if (isKaslrRegionAddr(addr, i)) {
                if (delta >= regionSize[i] >> regionAlignBits[i]) {
                    panic("Too large delta %lx\n", delta);
                }
                return (addr & regionMask[i]) | (delta << regionAlignBits[i]);
            }
        }
        return addr;
    }

    bool protectKaslrValidDirty(Addr addr) {
        const Addr addrMask = 0xffffffffc1ffffff;
        const Addr textMin = 0xffffffff80000000;
        const Addr textEnd = 0xffffffff82000000;
        const Addr textMax = 0xffffffffc0000000;
        if (!protectKaslr[0]) {
            return true;
        }
        // This function is only used to check when protect KASLR is enabled,
        //   whether address in the KASLR randomization region is valid
        if (addr >= textMin && addr < textMax) {
            return (addr >= textMin + kaslrOffset && addr < textEnd + kaslrOffset);
        }
        return true;
    }

    bool protectKaslrValid(Addr addr, Addr delta) {
        // This function is only used to check when protect KASLR is enabled,
        //   whether address in the KASLR randomization region is valid
        return protectKaslrApplyDelta(addr, delta) == addr;
    }

    enum TextMemAccessType {
        TextFetch,
        TextLoad,
        TextStore,
        TextAmo,
        NumTextMemAccessType,
    };

    virtual void protectKaslrCheck(Addr addr, TextMemAccessType t) { };
    virtual void protectKaslrAssert() { };

    const char *textMemAccessTypeStr[NumTextMemAccessType] = {
            "Fetch", "Load", "Store", "Amo"};

    // [Shixin]

protected:

    /// Instruction count used for SPARC misc register
    /// @todo unify this with the counters that cpus individually keep
    Tick instCnt;

    // every cpu has an id, put it in the base cpu
    // Set at initialization, only time a cpuId might change is during a
    // takeover (which should be done from within the BaseCPU anyway,
    // therefore no setCpuId() method is provided
    int _cpuId;

    /** Each cpu will have a socket ID that corresponds to its physical location
     * in the system. This is usually used to bucket cpu cores under single DVFS
     * domain. This information may also be required by the OS to identify the
     * cpu core grouping (as in the case of ARM via MPIDR register)
     */
    const uint32_t _socketId;

    /** instruction side request id that must be placed in all requests */
    RequestorID _instRequestorId;

    /** data side request id that must be placed in all requests */
    RequestorID _dataRequestorId;

    /** An intrenal representation of a task identifier within gem5. This is
     * used so the CPU can add which taskId (which is an internal representation
     * of the OS process ID) to each request so components in the memory system
     * can track which process IDs are ultimately interacting with them
     */
    uint32_t _taskId;

    /** The current OS process ID that is executing on this processor. This is
     * used to generate a taskId */
    uint32_t _pid;

    /** Is the CPU switched out or active? */
    bool _switchedOut;

    /** Cache the cache line size that we get from the system */
    const unsigned int _cacheLineSize;

    /** Global CPU statistics that are merged into the Root object. */
    struct GlobalStats : public statistics::Group
    {
        GlobalStats(statistics::Group *parent);

        statistics::Value simInsts;
        statistics::Value simOps;

        statistics::Formula hostInstRate;
        statistics::Formula hostOpRate;
    };

    /**
     * Pointer to the global stat structure. This needs to be
     * constructed from regStats since we merge it into the root
     * group. */
    static std::unique_ptr<GlobalStats> globalStats;

  public:

    /**
     * Purely virtual method that returns a reference to the data
     * port. All subclasses must implement this method.
     *
     * @return a reference to the data port
     */
    virtual Port &getDataPort() = 0;

    /**
     * Purely virtual method that returns a reference to the instruction
     * port. All subclasses must implement this method.
     *
     * @return a reference to the instruction port
     */
    virtual Port &getInstPort() = 0;

    /** Reads this CPU's ID. */
    int cpuId() const { return _cpuId; }

    /** Reads this CPU's Socket ID. */
    uint32_t socketId() const { return _socketId; }

    /** Reads this CPU's unique data requestor ID */
    RequestorID dataRequestorId() const { return _dataRequestorId; }
    /** Reads this CPU's unique instruction requestor ID */
    RequestorID instRequestorId() const { return _instRequestorId; }

    /**
     * Get a port on this CPU. All CPUs have a data and
     * instruction port, and this method uses getDataPort and
     * getInstPort of the subclasses to resolve the two ports.
     *
     * @param if_name the port name
     * @param idx ignored index
     *
     * @return a reference to the port with the given name
     */
    Port &getPort(const std::string &if_name,
                  PortID idx=InvalidPortID) override;

    /** Get cpu task id */
    uint32_t taskId() const { return _taskId; }
    /** Set cpu task id */
    void taskId(uint32_t id) { _taskId = id; }

    uint32_t getPid() const { return _pid; }
    void setPid(uint32_t pid) { _pid = pid; }

    inline void workItemBegin() { baseStats.numWorkItemsStarted++; }
    inline void workItemEnd() { baseStats.numWorkItemsCompleted++; }
    // @todo remove me after debugging with legion done
    Tick instCount() { return instCnt; }

  protected:
    std::vector<BaseInterrupts*> interrupts;

  public:
    BaseInterrupts *
    getInterruptController(ThreadID tid)
    {
        if (interrupts.empty())
            return NULL;

        assert(interrupts.size() > tid);
        return interrupts[tid];
    }

    virtual void wakeup(ThreadID tid) = 0;

    void postInterrupt(ThreadID tid, int int_num, int index);

    void
    clearInterrupt(ThreadID tid, int int_num, int index)
    {
        interrupts[tid]->clear(int_num, index);
    }

    void
    clearInterrupts(ThreadID tid)
    {
        interrupts[tid]->clearAll();
    }

    bool
    checkInterrupts(ThreadID tid) const
    {
        return FullSystem && interrupts[tid]->checkInterrupts();
    }

  protected:
    std::vector<ThreadContext *> threadContexts;

    trace::InstTracer * tracer;

  public:


    /** Invalid or unknown Pid. Possible when operating system is not present
     *  or has not assigned a pid yet */
    static const uint32_t invldPid = std::numeric_limits<uint32_t>::max();

    /// Provide access to the tracer pointer
    trace::InstTracer * getTracer() { return tracer; }

    /// Notify the CPU that the indicated context is now active.
    virtual void activateContext(ThreadID thread_num);

    /// Notify the CPU that the indicated context is now suspended.
    /// Check if possible to enter a lower power state
    virtual void suspendContext(ThreadID thread_num);

    /// Notify the CPU that the indicated context is now halted.
    virtual void haltContext(ThreadID thread_num);

    /// Given a Thread Context pointer return the thread num
    int findContext(ThreadContext *tc);

    /// Given a thread num get tho thread context for it
    virtual ThreadContext *getContext(int tn) { return threadContexts[tn]; }

    /// Get the number of thread contexts available
    unsigned
    numContexts()
    {
        return static_cast<unsigned>(threadContexts.size());
    }

    /// Convert ContextID to threadID
    ThreadID
    contextToThread(ContextID cid)
    {
        return static_cast<ThreadID>(cid - threadContexts[0]->contextId());
    }

  public:
    PARAMS(BaseCPU);
    BaseCPU(const Params &params, bool is_checker = false);
    virtual ~BaseCPU();

    void init() override;
    void startup() override;
    void regStats() override;

    void regProbePoints() override;

    void registerThreadContexts();

    // Functions to deschedule and reschedule the events to enter the
    // power gating sleep before and after checkpoiting respectively.
    void deschedulePowerGatingEvent();
    void schedulePowerGatingEvent();

    /**
     * Prepare for another CPU to take over execution.
     *
     * When this method exits, all internal state should have been
     * flushed. After the method returns, the simulator calls
     * takeOverFrom() on the new CPU with this CPU as its parameter.
     */
    virtual void switchOut();

    /**
     * Load the state of a CPU from the previous CPU object, invoked
     * on all new CPUs that are about to be switched in.
     *
     * A CPU model implementing this method is expected to initialize
     * its state from the old CPU and connect its memory (unless they
     * are already connected) to the memories connected to the old
     * CPU.
     *
     * @param cpu CPU to initialize read state from.
     */
    virtual void takeOverFrom(BaseCPU *cpu);

    /**
     * Flush all TLBs in the CPU.
     *
     * This method is mainly used to flush stale translations when
     * switching CPUs. It is also exported to the Python world to
     * allow it to request a TLB flush after draining the CPU to make
     * it easier to compare traces when debugging
     * handover/checkpointing.
     */
    void flushTLBs();

    /**
     * Determine if the CPU is switched out.
     *
     * @return True if the CPU is switched out, false otherwise.
     */
    bool switchedOut() const { return _switchedOut; }

    /**
     * Verify that the system is in a memory mode supported by the
     * CPU.
     *
     * Implementations are expected to query the system for the
     * current memory mode and ensure that it is what the CPU model
     * expects. If the check fails, the implementation should
     * terminate the simulation using fatal().
     */
    virtual void verifyMemoryMode() const { };

    /**
     *  Number of threads we're actually simulating (<= SMT_MAX_THREADS).
     * This is a constant for the duration of the simulation.
     */
    ThreadID numThreads;

    System *system;

    /**
     * Get the cache line size of the system.
     */
    inline unsigned int cacheLineSize() const { return _cacheLineSize; }

    /**
     * Serialize this object to the given output stream.
     *
     * @note CPU models should normally overload the serializeThread()
     * method instead of the serialize() method as this provides a
     * uniform data format for all CPU models and promotes better code
     * reuse.
     *
     * @param cp The stream to serialize to.
     */
    void serialize(CheckpointOut &cp) const override;

    /**
     * Reconstruct the state of this object from a checkpoint.
     *
     * @note CPU models should normally overload the
     * unserializeThread() method instead of the unserialize() method
     * as this provides a uniform data format for all CPU models and
     * promotes better code reuse.

     * @param cp The checkpoint use.
     */
    void unserialize(CheckpointIn &cp) override;

    /**
     * Serialize a single thread.
     *
     * @param cp The stream to serialize to.
     * @param tid ID of the current thread.
     */
    virtual void serializeThread(CheckpointOut &cp, ThreadID tid) const {};

    /**
     * Unserialize one thread.
     *
     * @param cp The checkpoint use.
     * @param tid ID of the current thread.
     */
    virtual void unserializeThread(CheckpointIn &cp, ThreadID tid) {};

    virtual Counter totalInsts() const = 0;

    virtual Counter totalOps() const = 0;

    /**
     * Schedule an event that exits the simulation loops after a
     * predefined number of instructions.
     *
     * This method is usually called from the configuration script to
     * get an exit event some time in the future. It is typically used
     * when the script wants to simulate for a specific number of
     * instructions rather than ticks.
     *
     * @param tid Thread monitor.
     * @param insts Number of instructions into the future.
     * @param cause Cause to signal in the exit event.
     */
    void scheduleInstStop(ThreadID tid, Counter insts, std::string cause);

    /**
     * Schedule simpoint events using the scheduleInstStop function.
     *
     * This is used to raise a SIMPOINT_BEGIN exit event in the gem5 standard
     * library.
     *
     * @param inst_starts A vector of number of instructions to start simpoints
     */

    void scheduleSimpointsInstStop(std::vector<Counter> inst_starts);

    /**
     * Schedule an exit event when any threads in the core reach the max_insts
     * instructions using the scheduleInstStop function.
     *
     * This is used to raise a MAX_INSTS exit event in thegem5 standard library
     *
     * @param max_insts Number of instructions into the future.
     */
    void scheduleInstStopAnyThread(Counter max_insts);

    /**
     * Get the number of instructions executed by the specified thread
     * on this CPU. Used by Python to control simulation.
     *
     * @param tid Thread monitor
     * @return Number of instructions executed
     */
    uint64_t getCurrentInstCount(ThreadID tid);

  public:
    /**
     * @{
     * @name PMU Probe points.
     */

    /**
     * Helper method to trigger PMU probes for a committed
     * instruction.
     *
     * @param inst Instruction that just committed
     * @param pc PC of the instruction that just committed
     */
    virtual void probeInstCommit(const StaticInstPtr &inst, Addr pc);

   protected:
    /**
     * Helper method to instantiate probe points belonging to this
     * object.
     *
     * @param name Name of the probe point.
     * @return A unique_ptr to the new probe point.
     */
    probing::PMUUPtr pmuProbePoint(const char *name);

    /**
     * Instruction commit probe point.
     *
     * This probe point is triggered whenever one or more instructions
     * are committed. It is normally triggered once for every
     * instruction. However, CPU models committing bundles of
     * instructions may call notify once for the entire bundle.
     */
    probing::PMUUPtr ppRetiredInsts;
    probing::PMUUPtr ppRetiredInstsPC;

    /** Retired load instructions */
    probing::PMUUPtr ppRetiredLoads;
    /** Retired store instructions */
    probing::PMUUPtr ppRetiredStores;

    /** Retired branches (any type) */
    probing::PMUUPtr ppRetiredBranches;

    /** CPU cycle counter even if any thread Context is suspended*/
    probing::PMUUPtr ppAllCycles;

    /** CPU cycle counter, only counts if any thread contexts is active **/
    probing::PMUUPtr ppActiveCycles;

    /**
     * ProbePoint that signals transitions of threadContexts sets.
     * The ProbePoint reports information through it bool parameter.
     * - If the parameter is true then the last enabled threadContext of the
     * CPU object was disabled.
     * - If the parameter is false then a threadContext was enabled, all the
     * remaining threadContexts are disabled.
     */
    ProbePointArg<bool> *ppSleeping;
    /** @} */

    enum CPUState
    {
        CPU_STATE_ON,
        CPU_STATE_SLEEP,
        CPU_STATE_WAKEUP
    };

    Cycles previousCycle;
    CPUState previousState;

    /** base method keeping track of cycle progression **/
    inline void
    updateCycleCounters(CPUState state)
    {
        uint32_t delta = curCycle() - previousCycle;

        if (previousState == CPU_STATE_ON) {
            ppActiveCycles->notify(delta);
        }

        switch (state) {
          case CPU_STATE_WAKEUP:
            ppSleeping->notify(false);
            break;
          case CPU_STATE_SLEEP:
            ppSleeping->notify(true);
            break;
          default:
            break;
        }

        ppAllCycles->notify(delta);

        previousCycle = curCycle();
        previousState = state;
    }

    // Function tracing
  private:
    bool functionTracingEnabled;
    std::ostream *functionTraceStream;
    Addr currentFunctionStart;
    Addr currentFunctionEnd;
    Tick functionEntryTick;
    void enableFunctionTrace();
    void traceFunctionsInternal(Addr pc);

  private:
    static std::vector<BaseCPU *> cpuList;   //!< Static global cpu list

  public:
    void
    traceFunctions(Addr pc)
    {
        if (functionTracingEnabled)
            traceFunctionsInternal(pc);
    }

    static int numSimulatedCPUs() { return cpuList.size(); }
    static Counter
    numSimulatedInsts()
    {
        Counter total = 0;

        int size = cpuList.size();
        for (int i = 0; i < size; ++i)
            total += cpuList[i]->totalInsts();

        return total;
    }

    static Counter
    numSimulatedOps()
    {
        Counter total = 0;

        int size = cpuList.size();
        for (int i = 0; i < size; ++i)
            total += cpuList[i]->totalOps();

        return total;
    }

  public:
    struct BaseCPUStats : public statistics::Group
    {
        BaseCPUStats(statistics::Group *parent);
        // Number of CPU cycles simulated
        statistics::Scalar numCycles;
        statistics::Scalar numWorkItemsStarted;
        statistics::Scalar numWorkItemsCompleted;
    } baseStats;

  private:
    std::vector<AddressMonitor> addressMonitor;

  public:
    void armMonitor(ThreadID tid, Addr address);
    bool mwait(ThreadID tid, PacketPtr pkt);
    void mwaitAtomic(ThreadID tid, ThreadContext *tc, BaseMMU *mmu);
    AddressMonitor *
    getCpuAddrMonitor(ThreadID tid)
    {
        assert(tid < numThreads);
        return &addressMonitor[tid];
    }

    Cycles syscallRetryLatency;

    /** This function is used to instruct the memory subsystem that a
     * transaction should be aborted and the speculative state should be
     * thrown away.  This is called in the transaction's very last breath in
     * the core.  Afterwards, the core throws away its speculative state and
     * resumes execution at the point the transaction started, i.e. reverses
     * time.  When instruction execution resumes, the core expects the
     * memory subsystem to be in a stable, i.e. pre-speculative, state as
     * well. */
    virtual void
    htmSendAbortSignal(ThreadID tid, uint64_t htm_uid,
                       HtmFailureFaultCause cause)
    {
        panic("htmSendAbortSignal not implemented");
    }

  // Enables CPU to enter power gating on a configurable cycle count
  protected:
    void enterPwrGating();

    const Cycles pwrGatingLatency;
    const bool powerGatingOnIdle;
    EventFunctionWrapper enterPwrGatingEvent;
};

} // namespace gem5

#endif // __CPU_BASE_HH__
