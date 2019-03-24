#=========================================================================
# BehavioralTranslatorL2.py
#=========================================================================
# This translator convert the constraint DAG into a sensitivity group file
# that can be used to import the translated top module back to PyMTL.
# This pass writes to <top_module>.ssg file in the current directory.
# The key assumption made by this pass to gen constraints is that
# each signal written by an upblk depends on all the signals read by
# this upblk.
#
# Author : Peitian Pan
# Date   : Feb 19, 2019

from copy                    import copy

from pymtl                   import *
from pymtl.passes.simulation import GenDAGPass

from BehavioralTranslatorL1     import BehavioralTranslatorL1
from ..utility               import get_topmost_member

class BehavioralTranslatorL2( BehavioralTranslatorL1 ):

  # Override
  def __init__( s, top ):

    super( BehavioralTranslatorL2, s ).__init__( top )

    s.gen_behavioral_trans_l2_metadata( top )

  #-----------------------------------------------------------------------
  # gen_behavioral_trans_l2_metadata
  #-----------------------------------------------------------------------

  def gen_behavioral_trans_l2_metadata( s, top ):

    # Collect all vertices and edges of the constraint DAG
    top.apply( GenDAGPass() )

    seq_upblks  = top.get_all_update_on_edge()
    comb_upblks = ( top.get_all_update_blocks() | top._dag.genblks) - seq_upblks

    upblks = { 'CombPath' : comb_upblks, 'SeqPath' : seq_upblks }

    upblk_RD, upblk_WR, _ = top.get_all_upblk_metadata()

    for upblk, signal_list in top._dag.genblk_reads.iteritems():
      upblk_RD[ upblk ] = set( signal_list )

    for upblk, signal_list in top._dag.genblk_writes.iteritems():
      upblk_WR[ upblk ] = set( signal_list )

    # Replace some signals with their parent_obj
    # Example: s.in_.foo -> s.in_
    _upblk_RD, _upblk_WR = {}, {}

    for upblk, set_RD in upblk_RD.iteritems():
      _set_RD = set()
      for signal in set_RD:
        _set_RD.add( get_topmost_member( top, signal ) )
      _upblk_RD[ upblk ] = _set_RD

    for upblk, set_WR in upblk_WR.iteritems():
      _set_WR = set()
      for signal in set_WR:
        _set_WR.add( get_topmost_member( top, signal ) )
      _upblk_WR[ upblk ] = _set_WR
    
    upblk_RD, upblk_WR = _upblk_RD, _upblk_WR

    # Construct net structure for top
    s.behavioral.net = {}

    for path_type in ( 'CombPath', 'SeqPath' ):
      for upblk in upblks[ path_type ]:

        wr_signals = set()
        for wr_signal in upblk_WR[ upblk ]:
          wr_signals.add( ( wr_signal, path_type ) )

        for rd_signal in upblk_RD[ upblk ]:
          if rd_signal in s.behavioral.net:
            s.behavioral.net[ rd_signal ] |= copy( wr_signals )
          else:
            s.behavioral.net[ rd_signal ] = copy( wr_signals )

  #-----------------------------------------------------------------------
  # translate_behavioral
  #-----------------------------------------------------------------------

  def translate_behavioral( s, top ):

    super( BehavioralTranslatorL2, s ).translate_behavioral( top )

    # Initialize the output port sensitivity group to 'not connected'
    top_inports  = top.get_input_value_ports()
    top_outports = top.get_output_value_ports()

    ssg = {}

    for outport in top_outports:
      ssg[ outport ] = {}
      for inport in top_inports:
        ssg[ outport ][ inport ] =\
          { 'CombPath':False, 'SeqPath':False }

    # Flood the nets to figure out the connections between inports and
    # outports
    for inport in top_inports:
      s.flood_mark( inport, lambda signal: signal in top_outports,
        inport, 'CombPath', ssg )

    # For each outport, find out what inports it depends on
    constraint_src = []
    for outport in top_outports:
      inport_strs       = []
      inport_connection = []
      for inport in top_inports:
        comb = ssg[ outport ][ inport ][ 'CombPath' ]
        seq  = ssg[ outport ][ inport ][ 'SeqPath'  ]

        if   not comb and not seq: continue
        if   comb and seq:         prefix = 'B'
        elif comb and not seq:     prefix = 'C'
        elif not comb and seq:     prefix = 'S'

        inport_strs.append( s.__class__.rtlir_tr_var_name(
          inport._dsl.my_name
        ) )
        inport_connection.append( prefix )

      constraint_src.append( s.__class__.rtlir_tr_constraint(
        inport_strs, inport_connection,
        s.__class__.rtlir_tr_var_name( outport._dsl.my_name )
      ) )

    # Store the callback function return value for final assembly
    s.hierarchy.sensitive_group_src =\
        s.__class__.rtlir_tr_constraints(
          constraint_src
        )

  #-----------------------------------------------------------------------
  # flood_mark
  #-----------------------------------------------------------------------

  def flood_mark( s, cur, flt, inport, pre_path_type, ssg ):

    if not cur in s.behavioral.net: return
    for nxt, cur_path_type in s.behavioral.net[ cur ]:
      path_type = 'SeqPath' if cur_path_type == 'SeqPath' else pre_path_type
      if flt( nxt ):
        ssg[ nxt ][ inport ][ path_type ] = True
        continue
      s.flood_mark( nxt, flt, inport, path_type )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_constraint( in_strs, conn_strs, out_str ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_constraints( constraints ):
    raise NotImplementedError()
