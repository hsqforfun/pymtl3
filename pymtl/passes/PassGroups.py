from pymtl import *
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from SimpleTickPass import SimpleTickPass

SimpleSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
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

SimpleCLSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  SimpleTickPass(),
  Component.lock_in_simulation
]

from mamba.UnrollTickPass import UnrollTickPass
UnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  SimpleSchedPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

from mamba.HeuristicTopoPass import HeuristicTopoPass
HeuTopoUnrollSim = [
  Component.elaborate,
  GenDAGPass(),
  HeuristicTopoPass(),
  UnrollTickPass(),
  Component.lock_in_simulation
]

from mamba.TraceBreakingSchedTickPass import TraceBreakingSchedTickPass
TraceBreakingSim = [
  Component.elaborate,
  GenDAGPass(),
  TraceBreakingSchedTickPass(),
  Component.lock_in_simulation
]
