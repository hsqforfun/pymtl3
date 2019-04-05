#=========================================================================
# TranslationPass.py
#=========================================================================
# This pass takes the top module of a PyMTL component and translates it 
# into SystemVerilog.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : March 12, 2019

import os

from pymtl.passes import BasePass, PassMetadata
from SVRTLIRTranslator import SVRTLIRTranslator

def mk_TranslationPass( _SVRTLIRTranslator ):

  class _TranslationPass( BasePass ):

    def __call__( s, top ):

      if not hasattr( top, '_pass_sverilog_translation' ):
        top._pass_sverilog_translation = PassMetadata()

      translator = _SVRTLIRTranslator( top )
      translator.translate()

      module_name = translator._top_module_name
      output_file = module_name + '.sv'
      ssg_file    = module_name + '.ssg'

      with open( output_file, 'w', 0 ) as output:
        output.write( translator.hierarchy.src )
        output.flush()
        os.fsync( output )
        output.close()

      if 'sensitive_group_src' in translator.hierarchy.__dict__:

        with open( ssg_file, 'w', 0 ) as ssg:
          ssg.write( translator.hierarchy.sensitive_group_src )
          ssg.flush()
          os.fsync( ssg )
          ssg.close()

      top._translator = translator
      top._pass_sverilog_translation.translated = True

  return _TranslationPass

TranslationPass = mk_TranslationPass( SVRTLIRTranslator )
