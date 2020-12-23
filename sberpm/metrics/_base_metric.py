# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

import pandas as pd


class BaseMetric:
    """
    Base Class that will contains base metrics for every object.

    Parameters
    ----------
    data_holder : sberpm.DataHolder
        Object that contains the event log and the names of its necessary columns.

    time_unit : {'s'/'second', 'm'/'minute', 'h'/'hour', 'd'/'day', 'w'/'week'}
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

    def __init__(self, data_holder, time_unit):
        data_holder.check_or_calc_duration()
        self._data_holder = data_holder
        if time_unit in ('week', 'w'):
            self._time_unit = 604800
        elif time_unit in ('day', 'd'):
            self._time_unit = 86400
        elif time_unit in ('hour', 'h'):
            self._time_unit = 3600
        elif time_unit in ('minute', 'm'):
            self._time_unit = 60
        elif time_unit in ('second', 's'):
            self._time_unit = 1
        else:
            raise AttributeError(f'Unknown time unit: "{time_unit}"')
        self.metrics = None
        self._group_column = None
        self._group_data = None

        if data_holder.user_column:
            self._user_column = data_holder.user_column
        else:
            self._user_column = None

    def apply(self):
        """
        Does nothing
        """
        pass

    def calculate_time_metrics(self, std=False):
        """
        Calculates all possible time metrics for grouped object:
        total_duration: total time duration of grouped objects
        min_duration: min time duration of grouped objects
        max_duration: max time duration of grouped objects
        mean_duration: mean time duration of grouped objects
        median_duration: median time duration of grouped objects
        variance_duration: variance of time duration of grouped objects
        std_duration: std of time duration of grouped objects

        Returns
        -------
        result: pd.DataFrame
            Key: id of an event trace, columns: names of the metrics.
        """

        metrics_df = pd.DataFrame()
        temp = self._sum_by(self._group_data)
        metrics_df[self._group_column] = temp.index
        metrics_df['total_duration'] = temp.values
        metrics_df['min_duration'] = self._min_by(self._group_data).values
        metrics_df['max_duration'] = self._max_by(self._group_data).values
        metrics_df['mean_duration'] = self._mean_by(self._group_data).values
        metrics_df['median_duration'] = self._median_by(self._group_data)
        if std:
            metrics_df['variance_duration'] = self._variance_by(self._group_data).values
            metrics_df['std_duration'] = self._std_by(self._group_data).values
        return metrics_df

    def _calculate_time_metrics(self, metrics_df, grouped_data, std):
        """
        Calculates all possible time metrics for grouped object:
        sum_time: total time grouped object
        mean_time: mean time grouped object
        median_time: median time grouped object
        max_time: max time grouped object
        min_time: min time grouped object
        variance_time: variance time grouped object
        std_time: std time grouped object

        Parameters
        ----------
        metrics_df : pd.DataFrame

        grouped_data : pandas.core.groupby.GroupBy
            Data, grouped by some column.

        std: bool

        Returns
        -------
        result: pd.DataFrame
            Key: id of an event trace, columns: names of the metrics.
        """
        metrics_df['total_duration'] = self._sum_by(grouped_data).values
        metrics_df['min_duration'] = self._min_by(grouped_data).values
        metrics_df['max_duration'] = self._max_by(grouped_data).values
        metrics_df['mean_duration'] = self._mean_by(grouped_data).values
        metrics_df['median_duration'] = self._median_by(grouped_data).values
        if std:
            metrics_df['variance_duration'] = self._variance_by(grouped_data).values
            metrics_df['std_duration'] = self._std_by(grouped_data).values

    def sum_time(self):
        """
        Calculate total time
        """
        return self._sum_by(self._group_data)

    def mean_time(self):
        """
        Calculate mean time
        """
        return self._mean_by(self._group_data)

    def median_time(self):
        """
        Calculate median time
        """
        return self._median_by(self._group_data)

    def max_time(self):
        """
        Calculate max time
        """
        return self._max_by(self._group_data)

    def min_time(self):
        """
        Calculate min time
        """
        return self._min_by(self._group_data)

    def var_time(self):
        """
        Calculate variance time
        """
        return self._variance_by(self._group_data)

    def std_time(self):
        """
        Calculate std time
        """
        return self._std_by(self._group_data)

    def _sum_by(self, grouped_data):
        """
        Groups the data and calculates the sum of the aggregated data.

        Parameters
        ----------
        grouped_data: pandas.core.groupby.GroupBy
            Column used for grouping the data.

        Returns
        -------
        result: pd.Series
            Key: name of the column the data is grouped by, value: the metric's value.
        """
        return grouped_data[self._data_holder.duration_column].sum() / self._time_unit

    def _max_by(self, grouped_data):
        """
        Groups the data and calculates the maximum of the aggregated data.

        Parameters
        ----------
        grouped_data: pandas.core.groupby.GroupBy
            Column used for grouping the data.

        Returns
        -------
        result: pd.Series
            Key: name of the column the data is grouped by, value: the metric's value.
        """
        return grouped_data[self._data_holder.duration_column].max() / self._time_unit

    def _min_by(self, grouped_data):
        """
        Groups the data and calculates the minimum of the aggregated data.

        Parameters
        ----------
        grouped_data: pandas.core.groupby.GroupBy
            Column used for grouping the data.

        Returns
        -------
        result: pd.Series
            Key: name of the column the data is grouped by, value: the metric's value.
        """
        return grouped_data[self._data_holder.duration_column].min() / self._time_unit

    def _mean_by(self, grouped_data):
        """
        Groups the data and calculates the mean of the aggregated data.

        Parameters
        ----------
        grouped_data: pandas.core.groupby.GroupBy
            Column used for grouping the data.

        Returns
        -------
        result: pd.Series
            Key: name of the column the data is grouped by, value: the metric's value.
        """
        return grouped_data[self._data_holder.duration_column].mean() / self._time_unit

    def _median_by(self, grouped_data):
        """
        Groups the data and calculates the median of the aggregated data.

        Parameters
        ----------
        grouped_data: pandas.core.groupby.GroupBy
            Column used for grouping the data.

        Returns
        -------
        result: pd.Series
            Key: name of the column the data is grouped by, value: the metric's value.
        """
        return grouped_data[self._data_holder.duration_column].median() / self._time_unit

    def _variance_by(self, group_data):
        return group_data[self._data_holder.duration_column].var(ddof=0) / self._time_unit

    def _std_by(self, group_data):
        return group_data[self._data_holder.duration_column].std(ddof=0) / self._time_unit
