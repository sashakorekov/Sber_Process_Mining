# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd

from ._base_metric import BaseMetric


class UserMetric(BaseMetric):
    """
    Class that contains metrics connected with users.

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
    """

    def __init__(self, data_holder, time_unit='day'):
        super().__init__(data_holder, time_unit)
        self._group_column = data_holder.user_column
        self._group_data = self._data_holder.data.groupby(self._group_column)

    def apply(self, std=False):
        """
        Calculate all metrics:
        unique_activities_num: number of unique activity that a user worked on
        activities_count: number of all activities that a user worked on
        unique_ids_num: number unique ids that a user worked on
        workload_in_percent: workload of user in percent.
            Number of activities that user did divided by a total number of activities in the event log.
        total_duration: total time duration of grouped objects
        min_duration: min time duration of grouped objects
        max_duration: max time duration of grouped objects
        mean_duration: mean time duration of grouped objects
        median_duration: median time duration of grouped objects
        variance_duration: variance of time duration of grouped objects
        std_duration: std of time duration of grouped objects
        """
        if self.metrics is None:
            self.metrics = self.unique_activities() \
                .rename(columns={self._data_holder.activity_column: 'unique_activities'})
            self.metrics['unique_activities_num'] = self.metrics['unique_activities'].apply(len)
            self.metrics["activities_count"] = self.count_activities()[self._data_holder.activity_column].values
            self.metrics['unique_ids_num'] = self.nunique_id()[self._data_holder.id_column].values
            self.metrics['workload_in_percent'] = self.workload_in_percent().map('{:,.2f}'.format)
            self._calculate_time_metrics(self.metrics, self._group_data, std)
        return self.metrics

    def workload_in_percent(self):
        """
        Percentage of all transitions each user made.

        Returns
        -------
        result: pd.Series
            Key: user, value: the metric's value.
        """
        transitions_count = self._data_holder.data.groupby(
            by=self._data_holder.user_column)[self._data_holder.activity_column].count()
        return (transitions_count / transitions_count.sum() * 100).reset_index(drop=True)

    def count_activities(self):
        return self._group_data.agg({self._data_holder.activity_column: 'count'}).reset_index(drop=True)

    def unique_activities(self):
        return self._group_data.agg({self._data_holder.activity_column: set}).reset_index()

    def nunique_activity(self):
        """
        Productivity of each user. The number of unique activities each user worked on.

        Returns
        -------
        result: pd.Series
            Key: user, value: the metric's value.
        """
        return self._group_data.agg({self._data_holder.activity_column: 'nunique'}).reset_index(drop=True)

    def nunique_id(self):
        """
        Productivity of each user. The number of unique event traces each user worked on.

        Returns
        -------
        result: pd.Series
            Key: user, value: the metric's value.
        """
        return self._group_data.agg({self._data_holder.id_column: 'nunique'}).reset_index(drop=True)
