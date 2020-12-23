# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd
from ._cycle_metric import CycleMetric
from ._base_metric import BaseMetric


class ActivityMetric(BaseMetric):
    """
    Class that contains metrics connected with activities.

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

    _cycle_metric: CycleMetric
        Object of class CycleMetric that find cycles in event log
    """

    def __init__(self, data_holder, time_unit='day', cycle_length=None):
        super().__init__(data_holder, time_unit)
        self._cycle_metric = CycleMetric(data_holder, cycle_length)
        self._group_column = data_holder.activity_column
        self._group_data = self._data_holder.data.groupby(self._group_column)

    def apply(self, std=False):
        """
        Calculate all metrics:
        total_count: Total number of activity's occurrence in the event log.
        unique_ids_num: number of unique ids where the activity was
        cycle_percent: percent of cycles from total frequency of an activity
        unique_users_num: number of unique users that work on an activity
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
                .rename(columns={self._data_holder.id_column: 'unique_ids'})
            self.metrics['total_count'] = self.count().values
            self.metrics["unique_ids_num"] = self.metrics['unique_ids'].apply(len)
            dict_cycle = self.cycle()
            temp = self.metrics.apply(lambda x: dict_cycle[x[self._group_column]], axis=1)
            self.metrics['cycle_percent'] = (temp / self.metrics['total_count'] * 100).map('{:,.2f}'.format)
            if self._user_column:
                self.metrics['unique_users_num'] = self.nunique_users().values
            self._calculate_time_metrics(self.metrics, self._group_data, std)
        return self.metrics

    def count(self):
        """
        Calculate number of activity
        """
        return self._group_data[self._group_column].count()

    def nunique_users(self):
        """
        Calculate number of unique users worken on activity
        """
        return self._group_data[self._user_column].nunique()

    def cycle(self):
        return self._cycle_metric.find()[0]
