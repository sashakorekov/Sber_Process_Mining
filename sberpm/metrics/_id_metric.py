# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd
from ._base_metric import BaseMetric


class IdMetric(BaseMetric):
    """
    Class that contains metrics connected with ids.

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
    """

    def __init__(self, data_holder, time_unit='day'):
        super().__init__(data_holder, time_unit)
        self._group_column = data_holder.id_column
        self._group_data = self._data_holder.data.groupby(self._group_column)

    def apply(self, std=False):
        """
        Calculate all metrics:
        trace_length: length of a trace
        unique_activities_num: number of unique activities
        cycle_percent: percent of repeated (more than once) activities in the event trace
        unique_users_num: number of unique users
        total_duration: total time duration of grouped objects
        min_duration: min time duration of grouped objects
        max_duration: max time duration of grouped objects
        mean_duration: mean time duration of grouped objects
        median_duration: median time duration of grouped objects
        variance_duration: variance of time duration of grouped objects
        std_duration: std of time duration of grouped objects
        """

        if self.metrics is None:
            self.metrics = self._group_data.agg({self._data_holder.activity_column: tuple}).reset_index() \
                .rename(columns={self._data_holder.activity_column: 'trace'})
            self.metrics['trace_length'] = self.metrics['trace'].apply(len)
            self.metrics['unique_activities_num'] = self.metrics['trace'].apply(lambda x: len(set(x)))
            self.metrics['cycle_percent'] = \
                (1 - self.metrics['unique_activities_num'] / self.metrics['trace_length']) * 100
            if self._user_column:
                self.metrics['unique_users_num'] = self.nunique_users().values

            self._calculate_time_metrics(self.metrics, self._group_data, std)

        return self.metrics

    def len(self):
        """
        Calculate length of id
        """
        return self._group_data[self._data_holder.activity_column].count()

    def nunique_users(self):
        """
        Calculate number of unique users in id
        """
        return self._group_data[self._user_column].nunique()

    def unique_activities(self):
        """
        Calculate number of unique activities in id
        """
        return self._group_data[self._data_holder.activity_column].nunique()
