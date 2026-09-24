"""Experimental semantic affinity communities; never causal workflow edges."""

from .work_reconstruction import digest, require


def validate_parameters(parameters):
    require(set(parameters) == {"neighbors", "similarity", "area_resolution", "work_resolution", "seed"})
    require(type(parameters["neighbors"]) is int and 1 <= parameters["neighbors"] <= 64)
    require(0 < parameters["similarity"] <= 1 and 0 < parameters["area_resolution"] <= 10 and
            0 < parameters["work_resolution"] <= 10 and type(parameters["seed"]) is int)


def group_vectors(vectors, parameters):
    import networkx as nx
    import numpy as np
    import sklearn
    from sklearn.neighbors import NearestNeighbors

    validate_parameters(parameters)
    identities = sorted(vectors)
    graph = nx.Graph()
    graph.add_nodes_from(identities)
    if len(identities) > 1:
        matrix = np.asarray([vectors[k] for k in identities], dtype=np.float32)
        neighbors = NearestNeighbors(n_neighbors=min(len(identities), parameters["neighbors"] + 1),
                                     metric="cosine", algorithm="brute", n_jobs=1).fit(matrix)
        for offset in range(0, len(identities), 128):
            # Some local BLAS builds leave spurious floating-point flags set.
            # Inspect every actual value instead of accepting NaN as an edge.
            with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                distances, indexes = neighbors.kneighbors(matrix[offset:offset + 128])
            require(bool(np.isfinite(distances).all()) and bool((distances >= -0.000001).all())
                    and bool((distances <= 2.000001).all()), "INVALID_SIMILARITY")
            for relative, (ds, indices) in enumerate(zip(distances, indexes)):
                left = identities[offset + relative]
                for distance, index in sorted(zip(ds, indices), key=lambda pair: (round(float(pair[0]), 6), identities[pair[1]])):
                    right = identities[index]
                    weight = round(max(-1.0, min(1.0, 1.0 - float(distance))), 6)
                    if left != right and weight >= parameters["similarity"]:
                        graph.add_edge(left, right, weight=weight)

    def communities(part, resolution):
        # NetworkX subgraph views may iterate a membership set, whose order
        # changes with PYTHONHASHSEED. A fixed Louvain RNG seed alone is not
        # enough: canonicalize both nodes and neighbor insertion order.
        ordered = nx.Graph()
        ordered.add_nodes_from(sorted(part.nodes))
        ordered.add_weighted_edges_from(sorted(
            (min(a, b), max(a, b), value["weight"])
            for a, b, value in part.edges(data=True)))
        part = ordered
        if not part.number_of_edges():
            return [[node] for node in sorted(part.nodes)]
        result = nx.community.louvain_communities(part, resolution=resolution, seed=parameters["seed"])
        # Louvain may produce disconnected communities; split those explicitly.
        return sorted([sorted(component) for cluster in result
                       for component in nx.connected_components(part.subgraph(cluster))])

    areas = []
    for members in communities(graph, parameters["area_resolution"]):
        works = communities(graph.subgraph(members), parameters["work_resolution"])
        areas.append({"id": digest(["area", members]), "members": members,
                      "work_groups": [{"id": digest(["work", work]), "members": work} for work in works]})
    return {"engine": {"method": "cosine-knn-louvain-v2-ordered", "networkx": nx.__version__,
                       "sklearn": sklearn.__version__, "numpy": np.__version__},
            "authority": "inferred-affinity-only", "areas": areas,
            "node_count": len(identities), "edge_count": graph.number_of_edges(),
            "singleton_areas": sum(len(a["members"]) == 1 for a in areas),
            "edges": [{"left": min(a, b), "right": max(a, b), "similarity": v["weight"]}
                      for a, b, v in sorted(graph.edges(data=True))]}
