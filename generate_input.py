import networkx as nx
import random
import matplotlib.pyplot as plt
from networkx import path_graph, random_layout
        # or any integer
# import numpy
# numpy.random.seed(4812)


def partition(lst, n):
    division = len(lst) / float(n)
    return [lst[int(round(division * i)): int(round(division * (i + 1)))] for i in range(n)]

# lines = [line.rstrip('\n') for line in open("names.txt")]
# small = random.sample(lines, 30)

# H = nx.gnm_random_graph(30, (30**2)/4) # random graph
# H = nx.gnp_random_graph(30, 0.3)


# sizes = [5, 5, 5, 5, 5, 5]
# probs = [[1.00, 0, 0, 0, 0, 0],
#         [0, 1.00, 0, 0, 0, 0],
#         [0, 0, 1.00, 0, 0, 0],
#         [0, 0, 0, 1.00, 0, 0],
#         [0, 0, 0, 0, 1.00, 0],
#         [0, 0, 0, 0, 0, 1.00]]



def generate(bus, capacity, diag):
    sizes = [capacity for _ in range(bus)]
    probs = [[(1-diag) / (bus - 1) for _ in range(bus)] for _ in range(bus)]
    for i in range(bus):
        probs[i][i] = diag

    H = nx.stochastic_block_model(sizes, probs, seed=0)
    edges = list(H.edges)
    G2 = nx.Graph()
    G2.add_edges_from(edges)
    return G2



def writeGraph(graph, size,rowdyNum, bus, capacity):

    nodes = list(graph.nodes)
    out = partition(nodes, bus)

    path = "./inputs/{0}/graph.gml".format(size)
    nx.write_gml(graph, path)

    outputPath = './outputs/{0}.out'.format(size)
    with open(outputPath, 'w') as f:
        for item in out:
            f.write("%s\n" % item)

    rowdy = []
    for i in range(rowdyNum):
        samplesize = random.randint(2, 5)
        rowdy.append(random.sample(nodes, samplesize))

    paramPath = './inputs/{0}/parameters.txt'.format(size)
    with open(paramPath, 'w') as f:
        f.write("%s\n" % bus)
        f.write("%s\n" % capacity)
        for item in rowdy:
            f.write("%s\n" % item)

bus = 6
capacity = 5
small = generate(bus, capacity, 1)
writeGraph(small, "small", 20, bus, capacity)

# students = 800
bus = 20
capacity = 40
large = generate(bus, capacity, 1)
writeGraph(large, "large", 1500, bus, capacity)

# p = 0.9  score = 20%
# p = 1 score = 80%

# students = 400
bus = 20
capacity = 20
medium = generate(bus, capacity, 0.99)
writeGraph(medium, "medium", 800, bus, capacity)

# nx.draw(medium, with_labels=True, font_weight='bold')
# plt.show()