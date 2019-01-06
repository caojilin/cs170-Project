We generated the file with nx.stochastic_block_model function, to make sure the graph can be seperated into several communities, with more edges within each community than those across communities.
Function "generate" takes number of communities, community size and the percentage of edges within a community to all edges of it. The function generates a graph according these parameters.
Function "writeGraph" takes all the parameters inolved in generating the graph and print the graph into the graph.gml file and the list of all the rowdy groups to parameters.txt .
We call the two functions with different parameters corresponding to small, medium and large size. The three sets of data is generated as we expected.# cs170-Project
