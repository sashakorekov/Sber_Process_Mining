class ProcessCountVectorizer:
    """
    Class for vectorizing event traces using CountVectorizer algorithm.
    Vectors' dimension will be equal to the number of unique activities.

    Parameters
    ----------
    binary: bool, default=False
        If True, all non zero counts are set to 1.

    return_dataframe: bool, default=False
        If True, returns pandas Dataframe with IDs as index and activities as columns,
        otherwise returns numpy ndarray.

    Examples
    --------
    >>> import pandas as pd
    >>> from sberpm import DataHolder
    >>> from sberpm.ml.vectorizer import ProcessCountVectorizer
    >>> # Create data_holder
    >>> df = pd.DataFrame({
    ...     'id_column': [1, 1, 2, 2],
    ...     'activity_column':['st1', 'st2', 'st1','st3'],
    ...     'dt_column':[123456, 123457, 123458,123459]})
    >>> data_holder = DataHolder(df, 'id_column', 'activity_column', 'dt_column')
    >>> vectorizer = ProcessCountVectorizer()
    >>> embeddings = vectorizer.transform(data_holder)
    """

    def __init__(self, binary=False, return_dataframe=False):
        self._binary = binary
        self._return_dataframe = return_dataframe

    def transform(self, data_holder):
        """
        Gets embeddings of the event traces in given data_holder.

        Parameters
        ----------
        data_holder : DataHolder
            Object that contains the event log and the names of its necessary columns.

        Returns
        -------
        embeddings: pandas.DataFrame of numpy.ndarray, shape=[event_traces_num, unique_activities_num]
            List of vectorized event traces.
        """
        embeddings = data_holder.data.groupby([data_holder.id_column, data_holder.activity_column]).size().unstack()
        embeddings.fillna(0., inplace=True)
        embeddings = embeddings.astype(int)  # convert to int from float

        if self._binary:
            embeddings = embeddings.astype(bool).astype(int)

        if not self._return_dataframe:
            embeddings = embeddings.values

        return embeddings
