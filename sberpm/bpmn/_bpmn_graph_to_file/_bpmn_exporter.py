# Pydotplus Python module is used in this file.
#   Licence: MIT License
#   Link: https://github.com/carlos-jenkins/pydotplus

from ._petri_net_to_bpmn import petri_net_to_bpmn
from ._bpmn_to_dot import bpmn_to_graph
from ._bpmn_xml_maker import XMLMaker

from ...visual._types import GraphType

import warnings
from pydotplus import InvocationException


class BpmnExporter:
    """
    Converts a Petri net to BPMN graph and saves it to a .bpmn-file.

    Attributes
    ----------
    xml_maker: XMLMaker
        Object that transforms a bpmn graph to an xml representation.

    Examples
    --------
    >>> from sberpm.bpmn import BpmnExporter
    >>>
    >>> bpmn_exporter = BpmnExporter().apply_petri(petri_net)  # petri_net = alpha_miner.graph
    >>> bpmn_exporter.write('file_name.bpmn')
    >>> print(bpmn_exporter.get_string_representation())
    """

    def __init__(self):
        self.xml_maker = None

    def apply_petri(self, petri_net):
        """
        Converts a given Petri-net to BPMN graph.

        Parameters
        ----------
        petri_net : Graph
            Graph object that must represent a Petri-net.

        Returns
        -------
        self
        """
        if petri_net.type != GraphType.PETRI_NET:
            raise TypeError(f'Graphs of type "{GraphType.PETRI_NET}" only are supported.'
                            f'Given graph has type "{petri_net.type}".')

        bpmn_graph = petri_net_to_bpmn(petri_net)  # Graph of type 'BPMN'

        # Create pydot graph with coordinates
        pydot_plus_graph = bpmn_to_graph(bpmn_graph)
        pydot_plus_graph.set('rankdir', 'LR')
        pydot_plus_graph.set('splines', 'ortho')
        try:
            graph_dot_data_with_coordinates = pydot_plus_graph.create(prog='dot', format='dot')
        except InvocationException:
            warnings.simplefilter('always', RuntimeWarning)
            warnings.warn("Impossible to create orthogonal edges, splines will be created instead.", RuntimeWarning)
            pydot_plus_graph.set('splines', 'spline')
            graph_dot_data_with_coordinates = pydot_plus_graph.create(prog='dot', format='dot')

        # Transform pydot_graph to xml
        xml_maker = XMLMaker().load_dot_data(graph_dot_data_with_coordinates)
        xml_maker.make()

        self.xml_maker = xml_maker
        return self

    def write(self, filename):
        """
        Saves calculated BPMN graph in BPMN notation to a file.

        Parameters
        ----------
        filename : str
            Name of the file.
        """
        if self.xml_maker is None:
            raise RuntimeError('Call bpmn_exporter.apply_petri(graph) first.')
        else:
            self.xml_maker.write(filename)

    def get_string_representation(self):
        """
        Returns a string representation of BPMN notation of calculated BPMN graph.

        Returns
        -------
        result: str
            BPMN notation of the graph.
        """
        if self.xml_maker is None:
            raise RuntimeError('Call bpmn_exporter.apply_petri(graph) first.')
        else:
            return self.xml_maker.to_string()
