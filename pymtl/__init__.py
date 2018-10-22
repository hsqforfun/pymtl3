
from datatypes import *
from datatypes import _bitwidths

from dsl.ConstraintTypes import U, M, RD, WR
from dsl.Connectable     import Wire, InVPort, OutVPort, Interface
from dsl.RTLComponent    import RTLComponent

__all__ = [
  'U','M','RD','WR',
  'Wire', 'InVPort', 'OutVPort', 'Interface',

  'RTLComponent',
  #  'SimRTLPass',
  'SystemVerilogTranslationPass', 
  # SimpleImportPass only works on tranlsation-pass-generated
  # files. The user should use an import pass that works on
  # arbitrary Verilog files, which is not implemented yet.
  # 'ImportPass',  # Not implemented yet
  # 'PrintMetadataPass', 'EventDrivenPass',

  'sext', 'zext', 'clog2', 'concat',
  'mk_bits', 'Bits',
] + [ "Bits{}".format(x) for x in _bitwidths ]
