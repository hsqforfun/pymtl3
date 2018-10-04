from pymtl                import *
from pymtl.model          import ComponentLevel1
from BasePass             import BasePass
from collections          import defaultdict, deque
from errors               import TranslationError

from ComponentTranslationPass import ComponentTranslationPass

class SystemVerilogTranslationPass( BasePass ):

  def __call__( s, top ):
    """ recursively translate the top module with name top """
    model_name            = top.__class__.__name__
    systemverilog_file    = model_name + '.sv'

    # Get all modules in the component hierarchy and translate the 
    # deepest component first

    nets = top.get_all_nets()
    adjs = top.get_signal_adjacency_dict()

    connections_self_child    = defaultdict(set)
    connections_self_self     = defaultdict(set)
    connections_child_child   = defaultdict(set)

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop()
        writer_host         = u.get_host_component()
        writer_host_parent  = writer_host.get_parent_object() 

        for v in adjs[u]:
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host         = v.get_host_component()
            reader_host_parent  = reader_host.get_parent_object()

            if writer_host is reader_host:
              connections_self_self[ writer_host ].add( ( u, v ) )

            elif writer_host_parent is reader_host:
              connections_self_child[ reader_host ].add( ( u, v ) )

            elif writer_host is reader_host_parent:
              connections_self_child[ writer_host ].add( ( u, v ) )

            elif writer_host_parent == reader_host_parent:
              connections_child_child[ writer_host_parent ].add( ( u, v ) )

            else: assert False

    ret = ComponentTranslationPass( 
          connections_self_self, 
          connections_self_self,
          connections_child_child
        )( top )

    with open( systemverilog_file, 'w' ) as sv_out_file:
      sv_out_file.write( ret )

    top._translated = True

