#=========================================================================
# StructuralConnectionTransL1.py
#=========================================================================
# Translate the connections within one component into their backend 
# representation.
#
# Author : Peitian Pan
# Date   : March 19, 2019

from collections import defaultdict, deque

from BaseStructuralTrans import BaseStructuralTrans

class StructuralConnectionTransL1( BaseStructuralTrans ):

  def __init__( s, top ):

    super( StructuralConnectionTransL1, s ).__init__( top )

    s.structural.connections_self_self = defaultdict(set)
    s.gen_connection_trans_l1_metadata( top )

  def translate( s ):

    super( StructuralConnectionTransL1, s ).translate()

    s.translate_self_self_connections( s.top )

  #-----------------------------------------------------------------------
  # gen_connection_trans_l1_metadata
  #-----------------------------------------------------------------------

  def gen_connection_trans_l1_metadata( s, top ):

    nets = top.get_all_nets()
    adjs = top.get_signal_adjacency_dict()

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop()
        writer_host        = u.get_host_component()
        writer_host_parent = writer_host.get_parent_object() 

        for v in adjs[u]:
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host        = v.get_host_component()
            reader_host_parent = reader_host.get_parent_object()

            # Four possible cases for the reader and writer signals:
            # 1.   They have the same host component. Both need 
            #       to be added to the host component.
            # 2/3. One's host component is the parent of the other.
            #       Both need to be added to the parent component.
            # 4.   They have the same parent component.
            #       Both need to be added to the parent component.

            if writer_host is reader_host:
              s.structural.connections_self_self[ writer_host ].add( ( u, v ) )

  #-----------------------------------------------------------------------
  # translate_self_self_connections
  #-----------------------------------------------------------------------

  def translate_self_self_connections( s, m ):

    connections_self_self = []
    connect_order = m.get_connect_order()

    ordered_conns   = [ '' for x in xrange(len(connect_order)) ]
    unordered_conns = []

    # Generate an ordered list of connections
    for writer, reader in s.structural.connections_self_self[m]:

      if ConnectionTransL1.is_in_list( (writer, reader), connect_order ):
        pos = ConnectionTransL1.get_pos( (writer,reader), connect_order )
        ordered_conns[pos] = (writer, reader)

      else:
        unordered_conns.append( (writer, reader) )

    for writer, reader in ordered_conns + unordered_conns:
      connections_self_self.append( s.__class__.rtlir_tr_connection_self_self(
        s.dtype_tr_signal( writer ), s.dtype_tr_signal( reader )
      ) )

    s.component[m].connections_self_self =\
      s.__class__.rtlir_tr_connections_self_self( connections_self_self )

    for child in m.get_child_components():
      s.translate_self_self_connections( child )

  #-----------------------------------------------------------------------
  # is_in_list
  #-----------------------------------------------------------------------

  @staticmethod
  def is_in_list( pair, List ):
    for u, v in List:
      if (u is pair[0] and v is pair[1]) or (u is pair[1] and v is pair[0]):
        return True
    return False

  #-----------------------------------------------------------------------
  # get_pos
  #-----------------------------------------------------------------------

  @staticmethod
  def get_pos( pair, List ):
    for idx, (u, v) in enumerate(List):
      if (u is pair[0] and v is pair[1]) or (u is pair[1] and v is pair[0]):
        return idx
    assert False

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_connections_self_self( connections_self_self ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_connection_self_self( wr_signal, rd_signal ):
    raise NotImplementedError()
