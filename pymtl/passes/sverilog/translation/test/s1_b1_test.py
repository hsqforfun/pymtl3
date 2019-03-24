#=========================================================================
# s1_b1_test.py
#=========================================================================
# Pure behavioral tests with value ports and no connections

import pytest

from pymtl import *
from pymtl.passes.utility.test_utility import gen_translation_pass,\
                                              run_translation_test, do_test

from ..SVRTLIRTranslator import mk_SVRTLIRTranslator
from ..TranslationPass   import mk_TranslationPass
from ....                import SimpleImportPass

# Reuse tests
from pymtl.passes.rtlir.translation.behavioral.test.rtlir_test import \
  test_mismatch_width_assign, test_slicing_basic, test_multi_upblks

def local_do_test( m ):

  translation_pass = gen_translation_pass(
    mk_TranslationPass, mk_SVRTLIRTranslator, 1, 1
  )

  run_translation_test( m, m._test_vector, translation_pass, SimpleImportPass )
