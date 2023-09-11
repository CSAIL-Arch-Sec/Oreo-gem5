/*
 * Copyright (c) 2007 The Hewlett-Packard Development Company
 * All rights reserved.
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

#ifndef __ARCH_X86_PCSTATE_HH__
#define __ARCH_X86_PCSTATE_HH__

#include "arch/generic/pcstate.hh"
#include "sim/serialize.hh"

namespace gem5
{

namespace X86ISA
{

class PCState : public GenericISA::UPCState<8>
{
  protected:
    using Base = GenericISA::UPCState<8>;

    uint8_t _size;
//    bool _dirtyNPC = false;

    Addr _kaslrCorrDelta = 0; // NOTE: This can be archDelta for pc!!!
    Addr _kaslrNpcDelta = 0;

  public:
    void
    output(std::ostream &os) const override
    {
        Base::output(os);
        ccprintf(os, ".%d.(%lx=>%lx)", this->size(), this->kaslrCorrDelta(), this->kaslrNpcDelta());
    }

    PCStateBase *clone() const override { return new PCState(*this); }

    void
    update(const PCStateBase &other) override
    {
        Base::update(other);
        auto &pcstate = other.as<PCState>();
        _size = pcstate._size;
        _kaslrCorrDelta = pcstate._kaslrCorrDelta;
        _kaslrNpcDelta = pcstate._kaslrNpcDelta;
    }

    void
    set(Addr val)
    {
        Base::set(val);
        _size = 0;
        _kaslrCorrDelta = 0;
        _kaslrNpcDelta = 0;
    }

    PCState(const PCState &other) :
        Base(other),
        _size(other._size),
        _kaslrCorrDelta(other._kaslrCorrDelta),
        _kaslrNpcDelta(other._kaslrNpcDelta) {}

    PCState &operator=(const PCState &other) = default;
    PCState() {}
    explicit PCState(Addr val) { set(val); }

//    void npc(Addr val) override {
//        _npc = val;
//        dirtyNPC(true);
//    }
//    bool dirtyNPC() const { return _dirtyNPC; }
//    void dirtyNPC(bool b) { _dirtyNPC = b; }

    void kaslrCorrDelta(Addr val) { _kaslrCorrDelta = val; }
    Addr kaslrCorrDelta() const { return _kaslrCorrDelta; }

    void kaslrNpcDelta(Addr val) { _kaslrNpcDelta = val; }
    Addr kaslrNpcDelta() const { return _kaslrNpcDelta; }

    void kaslrClearDelta() {
        _kaslrCorrDelta = 0;
        _kaslrNpcDelta = 0;
    }

    void
    setNPC(Addr val)
    {
        Base::setNPC(val);
        _size = 0;
        _kaslrCorrDelta = 0;
        _kaslrNpcDelta = 0;
//        dirtyNPC(true);
    }

    uint8_t size() const { return _size; }
    void size(uint8_t newSize) { _size = newSize; }

    bool
    branching() const override
    {
        return (this->npc() != this->pc() + size()) ||
               (this->nupc() != this->upc() + 1);
    }

    bool
    macroBranching() const
    {
        return !(this->npc() == this->pc() + size() ||
                (size() == 0 && this->npc() == this->pc() + 8));
    }

    void
    advance() override
    {
        Base::advance();
        _size = 0;
//        std::clog << "Advance" << std::endl;
        // TODO: Think about how advance should be like.
//        _kaslrCorrDelta = 0;
//        _kaslrNpcDelta = 0;
    }

    void
    uEnd()
    {
        Base::uEnd();
        _size = 0;
        // TODO: Think about how advance should be like.
//        std::clog << "uEnd " << _kaslrCorrDelta << " " << _kaslrNpcDelta << std::endl;
        _kaslrCorrDelta = _kaslrNpcDelta;
        _kaslrNpcDelta = 0;
    }

    void
    serialize(CheckpointOut &cp) const override
    {
        Base::serialize(cp);
        SERIALIZE_SCALAR(_size);
        SERIALIZE_SCALAR(_kaslrCorrDelta);
        SERIALIZE_SCALAR(_kaslrNpcDelta);
    }

    void
    unserialize(CheckpointIn &cp) override
    {
        Base::unserialize(cp);
        UNSERIALIZE_SCALAR(_size);
        UNSERIALIZE_SCALAR(_kaslrCorrDelta);
        UNSERIALIZE_SCALAR(_kaslrNpcDelta);
    }
};

} // namespace X86ISA
} // namespace gem5

#endif // __ARCH_X86_PCSTATE_HH__
