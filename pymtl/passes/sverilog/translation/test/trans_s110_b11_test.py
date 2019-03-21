#=========================================================================
# trans_s110_b11_test.py
#=========================================================================
# Pure behavioral tests with value ports and no connections

from pymtl import *
from pymtl.passes.utility.test_utility import gen_translation_pass,\
                                              run_translation_test, do_test

from ..SVRTLIRTrans    import mk_SVRTLIRTrans
from ..TranslationPass import mk_TranslationPass
from ....              import SimpleImportPass

# Reuse tests
# from design_test import test_adder
from pymtl.passes.rtlir.translation.behavioral.test.rtlir_test import *

structural_levels = { 'dtype':1, 'decl':1, 'connection':0 }
behavioral_levels = { 'upblk':1, 'constraint':1 }

def local_do_test( m ):

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTrans, structural_levels, behavioral_levels
  )

  run_translation_test( m, m._test_vector, translation_pass, SimpleImportPass )

# Skip the tests that do not belong to this level
map( pytest.mark.skip, [
  test_index_basic, test_index_bits_slicing, test_multi_components, test_for_basic
] )
