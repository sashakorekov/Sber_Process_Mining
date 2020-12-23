# Numpy Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/numpy/numpy

# Pandas Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/pandas-dev/pandas

# Scikit-learn Python module is used in this file.
#   Licence: BSD-3-Clause License
#   Link: https://github.com/scikit-learn/scikit-learn


from sklearn.cluster import KMeans
import pandas as pd
import numpy as np


class GraphClustering:
    """
    Class for clustering event traces.

    Parameters
    ----------
    method : {'kmeans'}, default='kmeans'
        Method used for clustering data.

    Attributes
    ----------
    _method: str
        Name of the method used for clustering.

    _model: object
        Object that contains the realization of the clustering algorithm.

    Examples
    --------
    >>> import pandas as pd
    >>> from sberpm import DataHolder
    >>> from sberpm.ml.vectorizer import ProcessCountVectorizer
    >>> from sberpm.ml.processes import GraphClustering
    >>> # Create data_holder
    >>> df = pd.DataFrame({
    ...     'id_column': [1, 1, 2, 2],
    ...     'activity_column':['st1', 'st2', 'st1','st3'],
    ...     'dt_column':[123456, 123457, 123458,123459]})
    >>> data_holder = DataHolder(df, 'id_column', 'activity_column', 'dt_column')
    >>> vectorizer = ProcessCountVectorizer()
    >>> embeddings = vectorizer.transform(data_holder)
    >>> model = GraphClustering()
    >>> model.fit(embeddings, max_cluster_num = 2)
    >>> labels = model.predict(embeddings)
    """

    def __init__(self, method='kmeans'):
        if method not in ['kmeans']:
            raise ValueError(f'Only "kmeans" method is supported, but received: "{method}"')
        self._method = method
        self._model = None

    def fit(self, embeddings, min_cluster_num=2, max_cluster_num=4, random_state=42):
        """
        Trains the model and searches for the optimal number of clusters.

        Parameters
        ----------
        embeddings: array-like of number, shape=[number of objects, vector dimension]
            List of vectorized objects.

        min_cluster_num : int, default=2
            Minimum number of clusters.

        max_cluster_num : int, default=4
            Maximum number of clusters.

        random_state: int, default=42

        Returns
        -------
        self
        """
        models = {}

        if self._method == 'kmeans':
            scores = []
            for k in range(min_cluster_num, max_cluster_num + 1):
                kmeans = KMeans(n_clusters=k, n_jobs=-1, random_state=random_state).fit(embeddings)
                scores.append(kmeans.inertia_)
                models[k - min_cluster_num] = kmeans

            self._model = models[np.argmax([scores[i - 1] / scores[i]
                                            for i in range(1, max_cluster_num - min_cluster_num + 1)])]

        return self

    def predict(self, embeddings):
        """
        Predict the clusters for given vectorized objects using trained algorithm.

        Parameters
        ----------
        embeddings: array-like of number, shape=[number of objects, vector dimension]
            List of vectorized objects.

        Returns
        -------
        labels: array-like of int, shape=[number of objects]
            Labels of the clusters.
        """
        return self._model.predict(embeddings)

    @staticmethod
    def add_cluster_column(data_holder, clusters, name_column='Process_clusters'):
        if data_holder.grouped_data is None:
            id_column = data_holder.id_column
            data_holder.grouped_data = pd.DataFrame({id_column: data_holder.data[id_column].unique()})
        data_holder.grouped_data[name_column] = clusters
        return data_holder

    def predict_add(self, data_holder, embeddings, name_column='Process_clusters'):
        if data_holder.grouped_data is None:
            id_column = data_holder.id_column
            data_holder.grouped_data = pd.DataFrame({id_column: data_holder.data[id_column].unique()})
        data_holder.grouped_data[name_column] = self._model.predict(embeddings)
        return data_holder
