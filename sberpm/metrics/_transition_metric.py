# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd
from ._base_metric import BaseMetric
from ._cycle_metric import CycleMetric


class TransitionMetric(BaseMetric):
    """
    Class that contains metrics connected with edges.

    Parameters
    ----------
    data_holder : DataHolder
        Object that contains the event log and the names of its necessary columns.

    time_unit : {'s'/'second', 'm'/'minute', 'h'/'hour', 'd'/'day', 'w'/'week'}, default='day'
        Calculate time in needed format.


    Attributes
    ----------
    _data_holder : DataHolder
        Object that contains the event log and the names of its necessary columns.

    _group_column : str
        Column used for grouping the data.

    _group_data: pandas.GroupBy object
        Object that contains pandas.GroupBy data grouping by _group_column.

    _user_column : str
        Column of users in event log.

    metrics: pd.DataFrame
        DataFrame contain all metrics that can be calculated

    _unique_edges: pd.Series
        Contain all edges of event log
    """

    def __init__(self, data_holder, time_unit='day', cycle_length=2):
        super().__init__(data_holder, time_unit)
        self._cycle_metric = CycleMetric(data_holder, cycle_length)
        self._group_column = data_holder.activity_column
        _edge_data = data_holder.data[
            [data_holder.id_column, data_holder.activity_column, data_holder.duration_column]].copy()
        if self._user_column:
            _edge_data.loc[:, self._user_column] = data_holder.data[self._user_column]

        if data_holder.start_timestamp_column is not None and data_holder.end_timestamp_column is None:
            start_activity_col = _edge_data[data_holder.activity_column]
            end_activity_col = _edge_data[data_holder.activity_column].shift(-1)
            start_id_col = _edge_data[data_holder.id_column]
            end_id_col = _edge_data[data_holder.id_column].shift(-1)
        else:
            start_activity_col = _edge_data[data_holder.activity_column].shift(1)
            end_activity_col = _edge_data[data_holder.activity_column]
            start_id_col = _edge_data[data_holder.id_column].shift(1)
            end_id_col = _edge_data[data_holder.id_column]

        _edge_data.loc[:, data_holder.activity_column] = tuple(start_activity_col + "-->" + end_activity_col)
        id_mask = start_id_col != end_id_col
        _edge_data.drop(_edge_data[id_mask].index, axis=0, inplace=True)

        self._unique_edges = _edge_data[self._group_column].unique()
        self._group_data = _edge_data.groupby(self._group_column)

    def apply(self, std=False):
        """        
        Calculate all metrics:
        total_count: frequency of edge
        total_duration: total time duration of grouped objects
        min_duration: min time duration of grouped objects
        max_duration: max time duration of grouped objects
        mean_duration: mean time duration of grouped objects
        median_duration: median time duration of grouped objects
        variance_duration: variance of time duration of grouped objects
        std_duration: std of time duration of grouped objects
        """
        if self.metrics is None:
            self.metrics = pd.DataFrame()
            self.metrics[self._group_column] = self._unique_edges
            self.metrics['total_count'] = self._group_data[self._group_column].count().values
            self._calculate_time_metrics(self.metrics, self._group_data, std)
            self.metrics[self._data_holder.activity_column] = self.metrics[self._data_holder.activity_column].apply(
                lambda x: self._split_tuple(x))
        return self.metrics.rename(columns={self._data_holder.activity_column: 'transition'}) \
            .sort_values('total_count', ascending=False).reset_index(drop=True)

    def calculate_time_metrics(self, std=False):
        """
        Calculate time metrics
        """
        metrics_df = super().calculate_time_metrics(std=std)
        metrics_df[self._data_holder.activity_column] = metrics_df[self._data_holder.activity_column].apply(
            lambda x: self._split_tuple(x))
        return metrics_df

    def count(self):
        """
        Count how many was edge
        """
        res = self._group_data[self._group_column].count()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    def nunique_users(self):
        return self._group_data[self._user_column].nunique()

    def sum_time(self):
        res = super().sum_time()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    def mean_time(self):
        res = super().mean_time()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    def median_time(self):
        res = super().median_time()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    def max_time(self):
        res = super().max_time()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    def min_time(self):
        res = super().min_time()
        res.index = [self._split_tuple(x) for x in res.index]
        return res

    @staticmethod
    def _split_tuple(x):
        """
        Split edges and transform edge from Activity1->Activity2 to tuple(Activity1,Activity2)
        """
        return tuple(x.split("-->"))

    def cycle(self):
        return self._cycle_metric.find()[1]

