#=========================================================================
# errors.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Jul 4, 2017

class PassOrderError( Exception ):
  """ Raise when applying a pass to a component and some required variable
      generated by other passes is missing """
  def __init__( self, var ):
    return super( PassOrderError, self ).__init__( \
    "Please first apply other passes to generate model.{}".format( var ) )

class ModelTypeError( Exception ):
  """ Raise when a pass cannot be applied to some component type """
  def __init__( self, typename ):
    return super( ModelTypeError, self ).__init__( \
    "This pass can only be applied to {}".format( typename ) )

class TranslationError( Exception ):
  """ Raise translation goes wrong """
  def __init__( self, blk, x ):
    return super( TranslationError, self ).__init__( \
    "{} {}".format( blk.__name__, x ) )

class VerilatorCompileError( Exception ):
	""" Compiling error for verilator """
	def __init__( self, err ):
		return super( VerilatorCompileError, self ).__init__( err )

class PyMTLImportError( Exception ):
  """ Raise error when import goes wrong """
  def __init__( self, err ):
    return super( PyMTLImportError, self ).__init__( err )

