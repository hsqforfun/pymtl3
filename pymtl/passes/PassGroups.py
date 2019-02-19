from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from SimpleTickPass import SimpleTickPass

SimpleSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

def SimpleSchedDumpDAGPass():
  def currying( top ):
    return SimpleSchedPass()( top, dump_graph = True )
  return currying

SimpleSimDumpDAG = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedDumpDAGPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

SimpleSimNoElaboration = [
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  RTLComponent.lock_in_simulation
]

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  RTLComponent.lock_in_simulation
]

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  RTLComponent.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  RTLComponent.lock_in_simulation
]
