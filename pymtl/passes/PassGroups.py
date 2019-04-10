from pymtl      import *
from simulation import GenDAGPass, SimpleSchedPass, SimpleTickPass 

#-------------------------------------------------------------------------
# SimpleSim
#-------------------------------------------------------------------------

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleSchedDumpDAG
#-------------------------------------------------------------------------

def SimpleSchedDumpDAGPass():
  def currying( top ):
    return SimpleSchedPass()( top, dump_graph = True )
  return currying

SimpleSimDumpDAG = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedDumpDAGPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleSimNoElaboration
#-------------------------------------------------------------------------

SimpleSimNoElaboration = [
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# SimpleCLSim
#-------------------------------------------------------------------------

SimpleCLSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# UnrollSim
#-------------------------------------------------------------------------

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# HeuTopoUnrollSim
#-------------------------------------------------------------------------

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

#-------------------------------------------------------------------------
# TraceBreakingSim
#-------------------------------------------------------------------------

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  Component.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  Component.lock_in_simulation
]
