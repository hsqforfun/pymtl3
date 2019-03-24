#=========================================================================
# TranslationPass.py
#=========================================================================
# This pass takes the top module of a PyMTL component and translates it 
# into SystemVerilog.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : March 12, 2019

from pymtl.passes import BasePass, PassMetadata
from SVRTLIRTranslator import SVRTLIRTranslator

def mk_TranslationPass( _SVRTLIRTranslator ):

  class _TranslationPass( BasePass ):

    def __call__( s, top ):

      if not hasattr( top, '_pass_sverilog_translation' ):
        top._pass_sverilog_translation = PassMetadata()

      translator = _SVRTLIRTranslator( top )
      translator.translate()

      module_name = translator.component[top].component_name
      output_file = module_name + '.sv'
      ssg_file    = module_name + '.ssg'

      with open( output_file, 'w' ) as output:
        output.write( translator.hierarchy.src )

      with open( ssg_file, 'w' ) as ssg:
        ssg.write( translator.hierarchy.sensitive_group_src )

      top._translator = translator
      top._pass_sverilog_translation.translated = True

  return _TranslationPass

TranslationPass = mk_TranslationPass( SVRTLIRTranslator )
