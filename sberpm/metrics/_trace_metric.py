# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd
from ._base_metric import BaseMetric


class TraceMetric(BaseMetric):
    """
    Class that contains metrics connected with traces.

    Parameters
    ----------
    data_holder : DataHolder
        Object that contains the event log and the names of its necessary columns.

    time_unit : {'s'/'second', 'm'/'minute', 'h'/'hour', 'd'/'day', 'w'/'week'}, default='day'
        Calculate time in needed format.

    cycle_length : int (default = None)
        Parameter for CycleMetric. If cycle_length is None CycleMetric find cycles of all lengths else of needed length.

    Attributes
    ----------
    _data_holder : sberpm.DataHolder
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
        # get work data for calculate
        grouped_data = data_holder.data.groupby(data_holder.id_column)
        work_data = grouped_data.agg({data_holder.activity_column: tuple}).reset_index()
        if self._user_column:
            work_data[data_holder.user_column] = grouped_data.agg({data_holder.user_column: tuple}).values
        work_data[data_holder.duration_column] = grouped_data[data_holder.duration_column].sum().values

        # group work data
        self._group_data = work_data.groupby(data_holder.activity_column)
        self._group_column = data_holder.activity_column

    def apply(self, std=False):
        """
        Calculate all metrics:
        total_count: total number of an event trace's occurrence in the event log
        trace_length: length of a trace
        unique_activities_num: number of unique activities in a trace
        cycle_percent: percent of repeated (more than once) activities in the event trace
        unique_users: set of unique users in a trace
        unique_users_num: number of unique users in a trace
        total_duration: total time duration of grouped objects
        min_duration: min time duration of grouped objects
        max_duration: max time duration of grouped objects
        mean_duration: mean time duration of grouped objects
        median_duration: median time duration of grouped objects
        variance_duration: variance of time duration of grouped objects
        std_duration: std of time duration of grouped objects
        """

        if self.metrics is None:
            self.metrics = self._group_data.agg({self._data_holder.id_column: set}).reset_index() \
                .rename(columns={self._data_holder.activity_column: 'trace',
                                 self._data_holder.id_column: 'unique_ids'})
            self.metrics['total_count'] = self.metrics['unique_ids'].apply(len).values
            self.metrics['trace_length'] = self.metrics['trace'].apply(len)
            self.metrics['unique_activities_num'] = self.metrics['trace'].apply(lambda x: len(set(x)))
            self.metrics['cycle_percent'] = \
                (1 - self.metrics['unique_activities_num'] / self.metrics['trace_length']) * 100

            if self._user_column:
                users = self._group_data[self._data_holder.user_column].apply(lambda x: set().union(*x))
                self.metrics["unique_users"] = users.apply(set).values
                self.metrics["unique_users_num"] = self.metrics['unique_users'].apply(len)
            self._calculate_time_metrics(self.metrics, self._group_data, std)

        return self.metrics.sort_values('total_count', ascending=False).reset_index(drop=True)

    def total_count(self):
        """
        Calculate number of occurrences of a trace.
        """
        return self._group_data[self._data_holder.id_column].count().sort_values(ascending=False)
