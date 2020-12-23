# Numpy Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/numpy/numpy

# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd
import numpy as np

from .._holder import DataHolder
from ..metrics import ActivityMetric, TransitionMetric


class AutoInsights:
    """
    Automatic insights search algorithm.

    Parameters
    ----------
    data_holder: sberpm.DataHolder
        The event log of the process. It must have three columns: id_column (unique id of a trace),
        activity_column (name of an activity in a trace), time_column (timestamp of an activity in a particular trace).

    time_unit: {'s'/'second', 'm'/'minute', 'h'/'hour', 'd'/'day', 'w'/'week'}, default='day'
        Time unit for representing the activities' durations.

    cycle_length: int, default=None
        Length of cycles to take into consideration.

    Examples
    --------
    >>>import pandas as pd
    >>>from sberpm import DataHolder
    >>>from sberpm.autoinsights import AutoInsights
    >>>from sberpm.visual import GraphvizPainter
    >>>from sberpm.miners import HeuMiner
    >>>data_holder = DataHolder("log.csv", 'Id', 'Activity', 'Dt', user_column='User', time_format='%Y-%m-%d %H:%M:%S')
    >>>miner = HeuMiner(data_holder, 0.8)
    >>>aut = AutoInsights(data_holder)
    >>>aut.apply(miner)
    >>>painter = GraphvizPainter()
    >>>painter.apply_insights(aut.get_graph())
    >>>painter.show()
    """

    def __init__(self, data_holder, time_unit='day', cycle_length=None):

        if type(data_holder) == DataHolder:
            self._data_holder = data_holder
            self._id_column = data_holder.id_column
            self._user_column = data_holder.user_column
            self._activity_column = data_holder.activity_column
        else:
            raise TypeError(f"data_holder must be of type DataHolder, but got: {type(data_holder)}")

        self._activity_metric = ActivityMetric(data_holder, time_unit, cycle_length)
        self._edge_metric = TransitionMetric(data_holder, time_unit)
        self._unique_activities = data_holder.get_unique_activities()
        self._time_unit = time_unit
        self.weights = {'count': 1, 'users_count': 1, 'mean_time': 1, 'cycle': 1}

        # pd.DataFrame, -1: good insight, 0: no insight, 1: bad insight.
        self._node_insights = None
        self._edge_insights = None

        self.graph = None

    def apply(self, miner, mode='overall', width_by_insight=True, q_min=0.1, q_top=0.85):
        """
        Calculates insights.

        Parameters
        ----------
        miner: sberpm.miners.SimpleMiner, sberpm.miners.CausalMiner, or sberpm.miners.HeuMiner
            DFG-Miner object (SimpleMiner, CausalMiner, or HeuMiner).

        mode: {'overall', 'time', 'cycles'}, default='overall'
            Mode for visualizing the insights.

        width_by_insight: bool, default=True
            If True, The edges' width on the graph will correspond to the "insight" status.

        q_min: float, default=0.1
            Quantile value for finding "good" insights (if value is smaller than q_min).

        q_top: float, default=0.85
            Quantile value for finding "bad" insights (if value is bigger than q_top).
        """
        node_name = 'activities'
        edge_name = 'edges'

        self.graph = self._get_miner_graph(miner)
        node_stats = self._get_stats(self._activity_metric, node_name)
        edge_stats = self._get_stats(self._edge_metric, edge_name)

        self._node_insights = self._get_insight(node_stats, q_min, q_top)
        self._edge_insights = self._get_insight(edge_stats, q_min, q_top)

        node_colors = self._get_color(node_stats, self._node_insights, mode, node_name)
        edge_colors = self._get_color(edge_stats, self._edge_insights, mode, edge_name)

        labels = self._calculate_edge_labels(edge_stats, mode, edge_name)

        for edge in self.graph.edges:
            self.graph.edges[edge].label = labels.get(edge)
            self.graph.edges[edge].color = edge_colors.get(edge)

        for node in self.graph.nodes:
            self.graph.nodes[node].color = node_colors.get(node)

        self._add_legend(edge_stats, mode)
        if width_by_insight:
            width = self._edge_insights[self._edge_insights.columns[1:-1]].apply(lambda x: sum(x), axis=1).abs()
            metric = {edge: value for edge, value in zip(self._edge_insights['edges'], width)}
            self.graph.add_edge_metric('insights', metric)

    def get_graph(self):
        return self.graph

    def describe_nodes(self):
        return self._node_insights

    def describe_edges(self):
        return self._edge_insights

    @staticmethod
    def _get_stats(metric, name_column):
        stats = pd.DataFrame()
        temp = metric.count()
        stats[name_column] = temp.index
        stats['count'] = tuple(temp)
        stats['mean_time'] = tuple(metric.mean_time())
        dict_cycle = metric.cycle()
        stats['cycle'] = stats.apply(lambda x: dict_cycle[x[name_column]], axis=1)
        if metric._user_column:
            stats['nunique_users'] = tuple(metric.nunique_users())
        return stats

    def _get_insight(self, stats, q_min, q_top):
        threshold_min, threshold_top = self._get_quantilies(stats, q_min, q_top)
        insights = pd.DataFrame()
        insights[stats.columns[0]] = stats[stats.columns[0]]
        for column in stats.columns[1:]:
            insights[column] = stats[column].apply(
                lambda x: self._insigth_by_quantile(x, threshold_min[column], threshold_top[column]))
        insights['insights'] = insights.apply(lambda x: self._sum_insight(x), axis=1)
        return insights

    @staticmethod
    def _get_miner_graph(miner):
        miner.apply()
        return miner.graph

    def _calculate_edge_labels(self, edge_stats, mode, edge_name):
        """
        Sets labels for edges.

        Parameters
        ----------
        mode: {'overall', 'cycles', 'time'}
            Parameters to use for determining the insights.

        Returns
        -------
        colors: dict of {str: str}
            Key: edge name, value: label.
        """
        if mode == 'cycles':
            labels = {}
        elif mode == 'time':
            labels = {edge: str(round(mean_time, 1)) + self._time_unit for edge, mean_time in
                      zip(edge_stats[edge_name], edge_stats['mean_time'])}
        elif mode == 'overall':
            labels = {}
            for edge, mean_time, cycle, insight in zip(edge_stats[edge_name], edge_stats['mean_time'],
                                                       edge_stats['cycle'], self._edge_insights['insights']):
                if insight == 1:
                    labels[edge] = str(round(mean_time, 1)) + self._time_unit
                    if cycle > 0:
                        labels[edge] += ', cycle'
        else:
            raise TypeError(f'Mode must be "overall", "cycles", or "time", but got {mode}')
        return labels

    @staticmethod
    def _get_color(stats, insights, mode, name_column):
        """
        Sets colors for objects (nodes or edges) according to their 'insight' status.

        Parameters
        ----------
        stats: pandas.DataFrame
            Objects with their metric values.

        insights: pandas.DataFrame
            Objects with their 'insight' status.

        mode: {'overall', 'cycles', 'time'}
            Parameters to use for determining the insights.

        Returns
        -------
        colors: dict of {str: {'red', 'grey', 'black'}}
            Colors for the objects according to their 'insight' status:
                'black': good insight (object's metric values are mostly small),
                'grey': no insight (object's metric values are mostly average)
                'red': bad insight (object's metric values are mostly big).
        """
        if mode == 'cycles':
            colors = {act: 'red' for act, cycle in zip(insights[name_column], stats['cycle']) if cycle > 0}
        else:
            i2c = {1: 'red', 0: 'grey', -1: 'black'}
            colors = {act: i2c[ins] for act, ins in zip(insights[name_column], insights['insights'])}
        return colors

    def _add_legend(self, stats, mode):
        """
        Adds two informational nodes to the graph.
        """
        if mode is not 'overall':
            return

        good_edges = [mean_time for mean_time, ins in zip(stats['mean_time'], self._edge_insights['insights']) if
                      ins < 0]
        bad_edges = [mean_time for mean_time, ins in zip(stats['mean_time'], self._edge_insights['insights']) if
                     ins > 0]
        good_time = np.nanmean(good_edges) if good_edges else 0
        bad_time = np.nanmean(bad_edges) if bad_edges else 0
        cycle_percent = np.mean(
            [cycle > 0 for cycle, ins in zip(stats['cycle'], self._edge_insights['insights']) if ins > 0])
        good_time = round(good_time, 1)
        bad_time = round(bad_time, 1)
        cycle_percent = round(cycle_percent * 100, 1)
        legend = {'good': 'good insights\nmean_time: {}{}\ncycle %: {}%'.format(
            good_time, self._time_unit, 0),
            'bad': 'bad insights\nmean_time: {}{}\ncycle %: {}%'.format(
                bad_time, self._time_unit, cycle_percent)}

        self.graph.add_node('legend_good', legend['good'])
        self.graph.add_node('legend_bad', legend['bad'])
        self.graph.nodes['legend_good'].color = 'black'
        self.graph.nodes['legend_bad'].color = 'red'

    @staticmethod
    def _get_quantilies(stats, q_min, q_top):
        return stats.quantile(q=q_min), stats.quantile(q=q_top)

    @staticmethod
    def _sign(x):
        if x > 0:
            return 1
        elif x < 0:
            return -1
        return 0

    @staticmethod
    def _insigth_by_quantile(x, th_min, th_top):
        if x < th_min:
            return -1
        elif x > th_top:
            return 1
        return 0

    def _sum_insight(self, x):
        res = 0
        for i in x.index[1:]:
            res += x[i]
        return self._sign(res)
