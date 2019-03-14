#=========================================================================
# RTLIRMetadataGenPass.py
#=========================================================================
# Generate the RTLIR metadata for a given PyMTL RTLComponent.
# It writes the following fields of the namespace _pass_rtlir_metadata_gen:
# .rtlir_upblks: a dict that maps an upblk to its rtlir representation
# .rtlir_types:  a dict that maps an object to its rtlir type
#
# Author : Peitian Pan
# Date   : March 11, 2019

from pymtl.passes import BasePass, PassMetadata
from pymtl.passes.utility import freeze

from RTLIRType import get_type
from UpblkRTLIRGenPass import UpblkRTLIRGenPass
from UpblkRTLIRTypeCheckPass import UpblkRTLIRTypeCheckPass

class RTLIRMetadataGenPass( BasePass ):

  def __call__( s, m ):

    if not hasattr( m, '_pass_rtlir_metadata_gen' ):
      m._pass_rtlir_metadata_gen = PassMetadata()

    s.top = m

    m._pass_rtlir_metadata_gen.rtlir_type_env =\
      s.generate_type_env( m )

    m._pass_rtlir_metadata_gen.rtlir_upblks = {}
    m._pass_rtlir_metadata_gen.rtlir_freevars = {}
    m._pass_rtlir_metadata_gen.rtlir_tmpvars = {}

    s.generate_rtlir_upblks(
      m, m._pass_rtlir_metadata_gen.rtlir_type_env
    )

  def generate_rtlir_upblks( s, m, type_env ):

    m.apply( UpblkRTLIRGenPass() )
    m.apply( UpblkRTLIRTypeCheckPass( type_env ) )

    s.top._pass_rtlir_metadata_gen.rtlir_upblks.update(
      m._pass_upblk_rtlir_gen.rtlir_upblks
    )

    s.top._pass_rtlir_metadata_gen.rtlir_freevars.update(
      m._pass_upblk_rtlir_type_check.rtlir_freevars
    )

    s.top._pass_rtlir_metadata_gen.rtlir_tmpvars.update(
      m._pass_upblk_rtlir_type_check.rtlir_tmpvars
    )

    for child in m.get_child_components():
      s.generate_rtlir_upblks( child, type_env )

  def generate_type_env( s, m ):

    ret = {}

    Type = get_type( m )
    ret[ freeze( m ) ] = Type
    ret.update( Type.type_env )

    return ret
