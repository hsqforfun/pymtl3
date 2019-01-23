#========================================================================
# RASTVisualizationPass.py
#========================================================================
# Visualize RAST using Graphviz packeage. The output graph is in PDF
# format. 
# This file is automatically generated by RASTImplGen.py.

import os
import RASTTypeSystem

from pymtl import *
from RAST import *
from BasePass import BasePass

from graphviz import Digraph

class RASTVisualizationPass( BasePass ):
  def __call__( s, model ):
    visitor = RASTVisualizationVisitor()

    for blk in model.get_update_blocks():
      visitor.init( blk.__name__ )
      visitor.visit( model._rast[ blk ] )
      visitor.dump()

class RASTVisualizationVisitor( RASTNodeVisitor ):
  def __init__( s ):
    s.output = 'unamed'
    s.output_dir = 'rast-viz'

  def init( s, name ):
    s.g = Digraph( 
      comment = 'RAST Visualization of ' + name,
      node_attr = { 'shape' : 'plaintext' }
    )
    s.blk_name = name
    s.cur = 0

  def dump( s ):
    if not os.path.exists( s.output_dir ):
      os.makedirs( s.output_dir )
    s.g.render( s.output_dir + os.sep + s.blk_name )

  def visit_BitOr( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">BitOr</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_Assign( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Assign</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
    for i, f in enumerate(node.targets):
      s.g.edge( str(local_cur), str(s.cur+1), label = 'targets[{idx}]'.format(idx = i) )
      s.visit( f )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'value' )
    s.visit( node.value )

  def visit_Module( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Module</TD></TR> <TR><TD>module</TD><TD>{module}</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail).format(module=node.module)

    s.g.node( str( s.cur ), label = label )

  def visit_ShiftLeft( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">ShiftLeft</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_BitAnd( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">BitAnd</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_Const( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Const</TD></TR> <TR><TD>nbits</TD><TD>{nbits}</TD></TR> <TR><TD>value</TD><TD>{value}</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail).format(nbits=node.nbits, value=node.value)

    s.g.node( str( s.cur ), label = label )

  def visit_Attribute( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Attribute</TD></TR> <TR><TD>attr</TD><TD>{attr}</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail).format(attr=node.attr)

    s.g.node( str( s.cur ), label = label )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'value' )
    s.visit( node.value )

  def visit_Sub( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Sub</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_Slice( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Slice</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'value' )
    s.visit( node.value )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'lower' )
    s.visit( node.lower )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'upper' )
    s.visit( node.upper )

  def visit_Index( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Index</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'value' )
    s.visit( node.value )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'idx' )
    s.visit( node.idx )

  def visit_Add( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">Add</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_BitXor( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">BitXor</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )

  def visit_BinOp( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">BinOp</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'left' )
    s.visit( node.left )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'op' )
    s.visit( node.op )
    s.g.edge( str(local_cur), str(s.cur+1), label = 'right' )
    s.visit( node.right )

  def visit_CombUpblk( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">CombUpblk</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
    for i, f in enumerate(node.body):
      s.g.edge( str(local_cur), str(s.cur+1), label = 'body[{idx}]'.format(idx = i) )
      s.visit( f )

  def visit_ShiftRightLogic( s, node ):
    s.cur += 1
    local_cur = s.cur

    table_header = '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0"> '
    table_body = '<TR><TD COLSPAN="2">ShiftRightLogic</TD></TR>'
    table_opt = ''
    table_trail = ' </TABLE>>'

    if isinstance( node.Type, RASTTypeSystem.BaseRASTType ):
      table_opt = ' <TR><TD COLSPAN="2">Type: ' + node.Type.__class__.__name__ + '</TD></TR>'
      for name, obj in node.Type.__dict__.iteritems():
        table_opt += ' <TR><TD>' + name + '</TD><TD>' + str( obj ) + '</TD></TR>'

    label = (table_header + table_body + table_opt + table_trail)

    s.g.node( str( s.cur ), label = label )
