import numpy as np


class Graph:

    def __init__(self, adjacency, rowlabels, columnlabels, matching=None):
        if matching is None:
            matching = []
        self.adjacency = np.array(adjacency)
        self.rowlabels = rowlabels
        self.columnlabels = columnlabels
        self.matching = matching

    def __str__(self):
        return str(self.adjacency)

    @classmethod
    def standard(cls, adjacency):
        """ Initialises a graph with trivial feasible labelling. """
        zeroed = np.zeros(len(adjacency))
        maxed = np.amax(adjacency, axis=0)
        return cls(adjacency, zeroed, maxed)

    @classmethod
    def more_standard(cls, adjacency, matching):
        """ Initialises a graph with trivial feasible labelling and
        matching in E_l. """
        zeroed = np.zeros(len(adjacency))
        maxed = np.amax(adjacency, axis=0)
        return cls(adjacency, zeroed, maxed, matching)

    def is_free(self, n, axis=0):
        """ Determines whether a vertex is free or not. """
        if axis == 0:
            index = [pair[0] for pair in self.matching]
        elif axis == 1:
            index = [pair[1] for pair in self.matching]
        else:
            raise KeyError

        return n not in index

    def is_perfect(self):
        """ Determines whether a matching is perfect or not. """
        # Probably doesn't work for non-square adjacency matrices
        return len(self.matching) == len(self.rowlabels)

    def extract_equality_graph(self):
        """ Produces the equality graph for a given labelled graph. """
        equality_graph = np.copy(self.adjacency)

        for i in range(len(self.rowlabels)):
            for j in range(len(self.columnlabels)):
                if self.rowlabels[i] + self.columnlabels[j] \
                        != self.adjacency[i][j]:
                    equality_graph[i][j] = 0  # Set to None

        return Graph(equality_graph, self.rowlabels, self.columnlabels,
                     matching=self.matching)

    def generate_matching(self):
        """ Returns a matching in a graph, skipping zeroes. """
        # Skipping zeroes will probably won't cause any errors.

        matching = []
        disabledrows = []
        disabledcolumns = []

        for i in range(len(self.rowlabels)):
            if i in disabledrows:
                continue
            for j in range(len(self.columnlabels)):
                if j in disabledcolumns:
                    continue
                elif self.adjacency[i][j] != 0:
                    matching += [[i, j]]
                    disabledrows += [i]
                    disabledcolumns += [j]
                    break

        self.matching = matching
        return matching

    def update_labels(self, subset_S, subset_T):
        """ Do some wacko shit to the labels to force N_l(S) != T """
        minima = []
        for i in subset_S:
            for j in range(len(self.columnlabels)):
                if j not in subset_T:
                    minima += [self.rowlabels[i] + self.columnlabels[j]
                               - self.adjacency[i, j]]

        delta = min(minima)

        for i in range(len(self.rowlabels)):
            if i in subset_S:
                self.rowlabels[i] -= delta

        for j in range(len(self.columnlabels)):
            if j in subset_T:
                self.columnlabels[j] += delta

        return self.rowlabels, self.columnlabels

    def old_augment(self, u, y):
        """ Use augment instead, this is trash. """
        a = u
        b = self.connect_unmatched(a, axis=0)
        while True:
            store = self.connect_matched(b, axis=1)
            self.matching.append([a, b])
            a = store
            if b == y:
                return self.matching
            store = self.connect_unmatched(a, axis=0)
            self.matching.remove([a, b])
            b = store

    def find_augmenting(self, initial, final, axis=0, touched=None):
        """ Returns an augmenting path from free vertices u and y. """
        if touched is None:
            touched = [[initial], []]
        path = []
        potential = []

        if axis == 0:
            for j in range(len(self.columnlabels)):
                if self.adjacency[initial][j] != 0 and \
                        [initial, j] not in self.matching and \
                        j not in touched[1]:
                    potential.append(j)

            if not potential:
                return [], False

            for middle in potential:
                touched[1].append(middle)
                recurse = self.find_augmenting(middle, final,
                                               axis=1, touched=touched)
                touched[1].remove(middle)
                if recurse[1]:
                    path = [[initial, middle]]

                    for pair in recurse[0]:
                        path += [pair]
                    return path, True

        elif axis == 1:
            if initial == final and axis == 1:
                return [], True

            for i in range(len(self.rowlabels)):
                if self.adjacency[i][initial] != 0 and \
                        [i, initial] in self.matching and \
                        i not in touched[0]:
                    potential.append(i)
                    break

            if not potential:
                return [], False

            for middle in potential:
                touched[0].append(middle)
                recurse = self.find_augmenting(middle, final,
                                               axis=0, touched=touched)
                touched[0].remove(middle)
                if recurse[1]:
                    path = [[middle, initial]]

                    for pair in recurse[0]:
                        path += [pair]
                    return path, True

        else:
            raise KeyError

        return path, False

    def augment(self, initial, final):
        """ Augments an augmenting path, swapping M with E-M. """
        path = self.find_augmenting(initial, final)[0]
        for i in range(len(path)):
            if i % 2 == 0:
                self.matching.append(path[i])
            else:
                self.matching.remove(path[i])

        return self.matching

    def connect_unmatched(self, a, axis=0):
        """ Return a vertex unmatched with a. """
        if axis == 0:
            for j in range(len(self.columnlabels)):
                if self.adjacency[a][j] != 0 and \
                        [a, j] not in self.matching:
                    return j
        elif axis == 1:
            for i in range(len(self.rowlabels)):
                if self.adjacency[i][a] != 0 and \
                        [i, a] not in self.matching:
                    return i
        else:
            raise KeyError
        return None

    def connect_matched(self, a, axis=0):
        """ Return a vertex matched with a. """
        if axis == 0:
            for pair in self.matching:
                if pair[0] == a:
                    return pair[1]
        elif axis == 1:
            for pair in self.matching:
                if pair[1] == a:
                    return pair[0]
        else:
            raise KeyError
        return None

    def neighbour(self, subset_S):
        """ Generates N_l(S). """
        neighbour = []
        for i in subset_S:
            for j in range(len(self.columnlabels)):
                if self.adjacency[i][j] != 0 and \
                        j not in neighbour:
                    neighbour += [j]
        return neighbour

    def hungarian_algorithm(self):
        """ Max-weight matching of a complete weighted
        bipartite graph. """
        equality_graph = self.extract_equality_graph()
        equality_graph.generate_matching()

        subset_S = []
        subset_T = []

        while True:
            if equality_graph.is_perfect():
                self.matching = equality_graph.matching
                return self.matching

            u = 0
            for i in range(len(self.rowlabels)):
                if equality_graph.is_free(i, axis=0):
                    u = i
                    subset_S = [u]
                    subset_T = []
                    break

            while True:
                # Generate N_l(S)
                neighbour = equality_graph.neighbour(subset_S)
                neighbour.sort()

                # Force labels to satisfy N_l(S) != T
                if neighbour == subset_T:
                    self.update_labels(subset_S, subset_T)
                    store_match = equality_graph.matching
                    equality_graph = self.extract_equality_graph()
                    equality_graph.matching = store_match
                    neighbour = equality_graph.neighbour(subset_S)
                    neighbour.sort()

                y = 0
                for j in range(len(self.columnlabels)):
                    if j in neighbour and j not in subset_T:
                        y = j
                        break

                if equality_graph.is_free(y, axis=1):
                    equality_graph.augment(u, y)  # Finish this thing
                    break
                else:
                    subset_S += [equality_graph.connect_matched(y, axis=1)]
                    subset_S.sort()
                    subset_T += [y]
                    subset_T.sort()

    def weight_sum(self):
        """ Sum of the weights in the matching. """
        return sum(self.adjacency[i][j] for i, j in self.matching)


if __name__ == "__main__":
    arrayA = [174, 521, 24, 224, 831, 179, 712, 97]
    arrayB = [281, 33, 122, 415, 611, 235, 737, 81]
    arrayXOR = xor_array(arrayA, arrayB)
    print(arrayXOR)
    print()
    G = Graph.standard(arrayXOR)
    print(G.hungarian_algorithm())
    print(G.weight_sum())
