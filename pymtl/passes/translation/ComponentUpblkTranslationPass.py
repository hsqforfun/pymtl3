#=========================================================================
# ComponentUpblkTranslationPass.py
#=========================================================================
# Translation pass for all update blocks within one component. 
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Oct 18, 2018

import ast

from pymtl             import *
from pymtl.dsl         import ComponentLevel1
from pymtl.passes      import BasePass, PassMetadata

from pymtl.passes.rast import ComponentUpblkRASTGenPass
from pymtl.passes.rast import ComponentUpblkRASTToSVPass
from pymtl.passes.rast import RASTVisualizationPass
from pymtl.passes.rast import ComponentUpblkRASTTypeCheckPass

from errors            import TranslationError

class ComponentUpblkTranslationPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """ translate all upblks in component m and return the source code
    string"""

    m._pass_component_upblk_translation = PassMetadata()
    m._pass_component_upblk_translation.blk_srcs = {}

    # Generate and visualize RAST
    ComponentUpblkRASTGenPass()( m )
    ComponentUpblkRASTTypeCheckPass( s.type_env )( m )
    RASTVisualizationPass()( m )
    ComponentUpblkRASTToSVPass()( m )

    # Copy generated SystemVerilog source code into this pass's namespace
    for blk in m.get_update_blocks():
      m._pass_component_upblk_translation.blk_srcs[ blk ] =\
        m._pass_component_upblk_rast_to_sv.sv[ blk ]