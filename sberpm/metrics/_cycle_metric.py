from collections import Counter


class CycleMetric:
    """
    Class that contains metrics connected with load of activities and transitions of the process.

    Parameters
    ----------
    data_holder : sberpm.DataHolder
        Object that contains the event log and the names of its necessary columns.

    cycle_length: int
        Length of cycles to be calculated.

    Attributes
    ----------
    _data_holder : sberpm.DataHolder
        Object that contains the event log and the names of its necessary columns.

    _cycle_length: int
        Length of cycles to be calculated.

    _unique_activities: pd.Series
        Series/List unique activities

    _chains: list
        Object that contains chains of activities
    """

    def __init__(self, data_holder, cycle_length=None):
        self._cycle_length = cycle_length
        self._chains = data_holder.get_grouped_data(data_holder.activity_column)[data_holder.activity_column].values
        self._unique_activities = data_holder.get_unique_activities()
        self._data_holder = data_holder

    def _get_indices_of_cyclic_element(self, chain, elem):
        return [i for i, x in enumerate(chain) if x == elem]

    def _get_length_of_cycle(self, chain, elem):
        ind = self._get_indices_of_cyclic_element(chain, elem)
        return ind[-1] - ind[0]

    def _count_chain(self, chain):
        counter = {}
        for elem in chain:
            counter[elem] = counter.get(elem, 0) + 1
        if self._cycle_length:
            doubles = {element: count for element, count in counter.items() if count > 1
                       and self._get_length_of_cycle(chain, element) == self._cycle_length}
        else:
            doubles = {element: count for element, count in counter.items() if count > 1}
        return doubles

    def find(self):
        # поиск минимального совокупного вхождения двух одинаковых вершин -- "подозрение" на цикл
        cyclic_nodes = Counter({})
        data = self._data_holder.data[
            [self._data_holder.id_column, self._data_holder.activity_column, self._data_holder.duration_column]]
        cyclic_edges = {i: 0 for i in set(
            zip(data[self._data_holder.activity_column], data[self._data_holder.activity_column].shift(-1)))}
        # поиск
        for chain in self._chains:
            cyclic_nodes_count_in_chain = self._count_chain(chain)
            elems = list(cyclic_nodes_count_in_chain.keys())
            for elem in elems:
                for i in self._get_indices_of_cyclic_element(chain, elem)[1:]:
                    try:
                        cyclic_edges[(chain[i - 1], chain[i])] += 1
                    except KeyError as e:
                        cyclic_edges[(chain[i - 1], chain[i])] = 1
            cyclic_nodes += Counter(cyclic_nodes_count_in_chain)

        for node in self._unique_activities:
            if node not in cyclic_nodes:
                cyclic_nodes[node] = 0

        return dict(cyclic_nodes), cyclic_edges
