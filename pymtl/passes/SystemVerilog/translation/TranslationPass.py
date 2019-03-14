#=========================================================================
# TranslationPass.py
#=========================================================================
# This pass takes the top module of a PyMTL component and translates it 
# into SystemVerilog.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : March 12, 2019

import inspect

from pymtl                                   import *
from pymtl.passes                            import BasePass, PassMetadata
from pymtl.passes.rtlir.TranslationFramework import RTLIRTranslator

from errors                                  import TranslationError
from TranslationCallbacks                    import TranslationCallbacks
from utility                                 import *

class TranslationPass( BasePass ):

  def __call__( s, top ):

    if not hasattr( top, '_pass_systemverilog_translation' ):
      top._pass_systemverilog_translation = PassMetadata()

    module_name = generate_module_name( top )
    output_file = module_name + '.sv'
    ssg_file    = module_name + '.ssg'

    translator = RTLIRTranslator( TranslationCallbacks() )
    translator.translate( top )

    with open( output_file, 'w' ) as output:
      output.write( translator.src )

    with open( ssg_file, 'w' ) as ssg:
      ssg.write( translator.constraint_src )

    top._pass_systemverilog_translation.translated = True
