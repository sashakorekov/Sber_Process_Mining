# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

from .._holder import DataHolder
from ._abstract_miner import AbstractMiner
from ..visual._graph import create_dfg

import pandas as pd


class HeuMiner(AbstractMiner):
    """
    Realization of Heuristic Miner algorithm.
    This algorithm is used to filter only the most "important" edges between the nodes.

    Parameters
    ----------
    data_holder : DataHolder
        Object that contains the event log and the names of its necessary columns.

    threshold : float, default=0.8
        Parameter of Heuristic miner. Ranges from 0 to 1.
        The bigger the threshold, the less edges will remain in the graph.

        For every edge the "importance" coefficient will be calculated, it ranges from -1 to 1.
        If it will be equal to or higher than the threshold, the edge will remain,
        otherwise it will be removed.

    Attributes
    ----------
    threshold: float
        Parameter of Heuristic miner. Ranges from 0 to 1.

    heu_df: pd.DataFrame or None
        Each row represents a unique pair of two activities (edge), contains the resulting coefficient and useful data.
        Columns:
        'a', 'b' - first and second activities in a pair,
        'a_b', 'b_a' - number of 'ab' and 'ba' pairs in the log ('b_a' column filled for loops only),
        'coeff' - resulting coefficient.
        
    Examples
    --------
    >>> import pandas as pd
    >>> from sberpm import DataHolder
    >>> from sberpm.miners import HeuMiner
    >>>
    >>> # Create data_holder
    >>> df = pd.DataFrame({
    ...     'id_column': [1, 1, 2],
    ...     'activity_column':['st1', 'st2', 'st1'],
    ...     'dt_column':[123456, 123457, 123458]})
    >>> data_holder = DataHolder(df, 'id_column', 'activity_column', 'dt_column')
    >>>
    >>> miner = HeuMiner(data_holder)
    >>> miner.apply()

    Notes
    -----
    This implementation includes the basic idea of calculating coefficients for edges and
    selecting the "important" ones using a threshold. It can also deal with cycles of lengths one and two.

    Some other possible features of the miner: the ability of heuristic miner to detect parallel activities,
    mining long-distant dependencies, noise cleaning -  are not implemented here.

    References
    ----------
    A.J.M.M. Weijters, W.M.P van der Aalst, and A.K. Alves de Medeiros.
    Process Mining with the Heuristics Miner-Algorithm, 2006

    https://pdfs.semanticscholar.org/1cc3/d62e27365b8d7ed6ce93b41c193d0559d086.pdf
    """

    def __init__(self, data_holder, threshold=0.8):
        super().__init__(data_holder)
        self.threshold = threshold
        self.heu_df = None  # ['a', 'b', 'a_b', 'b_a', 'coeff']

    def apply(self):
        """
        Starts the calculation of the graph using the heuristic miner.
        """
        unique_activities = self._data_holder.get_unique_activities()
        self.heu_df = self._calc_coeffs()

        graph = create_dfg()
        super().create_transitions(graph, unique_activities)
        super().create_start_end_events_and_edges(graph, *super()._get_first_last_activities())
        self._create_edges(graph)
        self.graph = graph

    def _calc_coeffs(self):
        df = pd.DataFrame()
        heu_df = pd.DataFrame()
        heu_df_len_2 = pd.DataFrame()

        df['id'] = self._data_holder.data[self._data_holder.id_column]
        df['a'] = self._data_holder.data[self._data_holder.activity_column]
        heu_df_len_1 = df.copy()
        heu_df_len_2 = df.copy()
        heu_df_len_1['b'] = df.groupby('id')['a'].shift(-1)
        heu_df_len_2['b'] = df.groupby('id')['a'].shift(-2)

        # calculate coeff for 2 loop
        heu_df_len_2 = heu_df_len_2.groupby(['a', 'b']).count().reset_index() \
            .rename(columns={'id': 'a>>b'})[['a', 'b', 'a>>b']]
        heu_df_len_2['b<<a'] = 0
        temp_a_b = (heu_df_len_2['a'] + ' -> ' + heu_df_len_2['b'])
        temp_b_a = (heu_df_len_2['b'] + ' -> ' + heu_df_len_2['a'])
        indexes = temp_a_b[temp_a_b.isin(temp_b_a) & (heu_df_len_2['a'] != heu_df_len_2['b'])].index
        for i in indexes:
            mask_b_a_row = (heu_df_len_2['a'] == heu_df_len_2['b'].iloc[i]) & \
                           (heu_df_len_2['b'] == heu_df_len_2['a'].iloc[i])
            heu_df_len_2.loc[i, 'b<<a'] = int(heu_df_len_2[mask_b_a_row]['a>>b'])
        heu_df_len_2['coeff'] = (heu_df_len_2['a>>b'] + heu_df_len_2['b<<a']) / \
                                (heu_df_len_2['a>>b'] + heu_df_len_2['b<<a'] + 1)

        # calculate coeff
        heu_df_len_1 = heu_df_len_1.groupby(['a', 'b']).count().reset_index() \
            .rename(columns={'id': 'a>b'})[['a', 'b', 'a>b']]
        heu_df_len_1['b<a'] = 0
        temp_a_b = (heu_df_len_1['a'] + ' -> ' + heu_df_len_1['b'])
        temp_b_a = (heu_df_len_1['b'] + ' -> ' + heu_df_len_1['a'])
        indexes = temp_a_b[temp_a_b.isin(temp_b_a) & (heu_df_len_1['a'] != heu_df_len_1['b'])].index

        # find self loop
        indexes_self_loop = temp_a_b[heu_df_len_1['a'] == heu_df_len_1['b']].index

        for i in indexes:
            mask_b_a_row = (heu_df_len_1['a'] == heu_df_len_1['b'].iloc[i]) & \
                           (heu_df_len_1['b'] == heu_df_len_1['a'].iloc[i])
            heu_df_len_1.loc[i, 'b<a'] = int(heu_df_len_1[mask_b_a_row]['a>b'])
        heu_df_len_1['coeff'] = (heu_df_len_1['a>b'] - heu_df_len_1['b<a']) / \
                                (heu_df_len_1['a>b'] + heu_df_len_1['b<a'] + 1)
        heu_df_len_1.loc[indexes_self_loop, 'coeff'] = heu_df_len_1['a>b'] / (heu_df_len_1['a>b'] + 1)

        heu_df_len_2['filter'] = heu_df_len_2.apply(
            lambda x: self._filter_func(x, list(zip(heu_df_len_1['a'], heu_df_len_1['b']))), axis=1)
        heu_df_len_2 = heu_df_len_2.dropna()
        # concate result
        heu_df = pd.concat([heu_df_len_1[['a', 'b', 'coeff']], heu_df_len_2[['a', 'b', 'coeff']]])

        return heu_df

    def _create_edges(self, graph):
        """
        Adds nodes and edges to the graph.
        """
        heu_df_filtered = self.heu_df[self.heu_df['coeff'] >= self.threshold][['a', 'b']]
        for a, b in zip(heu_df_filtered['a'].values, heu_df_filtered['b'].values):
            graph.add_edge(a, b)

    @staticmethod
    def _filter_func(x, pairs):
        if (x['a'], x['b']) in pairs or x['a'] == x['b']:
            return None
        else:
            return True
