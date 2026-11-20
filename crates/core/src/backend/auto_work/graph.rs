use super::{common::*, python_rng::PythonRandom};
use crate::backend::Result;
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
pub const GROUPING_METHOD: &str = "cosine-knn-louvain-v2-ordered";
fn number(value: &Value) -> Option<f64> {
    value
        .as_f64()
        .or_else(|| value.as_bool().map(|v| if v { 1.0 } else { 0.0 }))
}
pub fn validate_parameters(parameters: &Value) -> Result<()> {
    let expected = [
        "neighbors",
        "similarity",
        "area_resolution",
        "work_resolution",
        "seed",
    ]
    .into_iter()
    .collect::<BTreeSet<_>>();
    require(
        parameters.as_object().is_some_and(|object| {
            object.keys().map(String::as_str).collect::<BTreeSet<_>>() == expected
        }),
        "INVALID_INPUT",
    )?;
    require(
        parameters["neighbors"]
            .as_u64()
            .is_some_and(|n| (1..=64).contains(&n)),
        "INVALID_INPUT",
    )?;
    for (key, max) in [
        ("similarity", 1.0),
        ("area_resolution", 10.0),
        ("work_resolution", 10.0),
    ] {
        require(
            number(&parameters[key]).is_some_and(|n| n > 0.0 && n <= max),
            "INVALID_INPUT",
        )?;
    }
    let seed = parameters["seed"].to_string();
    require(
        parameters["seed"].is_number()
            && !seed.is_empty()
            && seed
                .trim_start_matches('-')
                .bytes()
                .all(|v| v.is_ascii_digit()),
        "INVALID_INPUT",
    )
}
#[derive(Clone)]
struct Graph {
    nodes: Vec<BTreeSet<usize>>,
    neighbors: Vec<Vec<(usize, f64)>>,
}
impl Graph {
    fn new(nodes: Vec<BTreeSet<usize>>) -> Self {
        let count = nodes.len();
        Self {
            nodes,
            neighbors: vec![Vec::new(); count],
        }
    }
    fn edge(&mut self, left: usize, right: usize, weight: f64) {
        if let Some((_, value)) = self.neighbors[left]
            .iter_mut()
            .find(|(node, _)| *node == right)
        {
            *value += weight;
        } else {
            self.neighbors[left].push((right, weight));
        }
        if left != right {
            if let Some((_, value)) = self.neighbors[right]
                .iter_mut()
                .find(|(node, _)| *node == left)
            {
                *value += weight;
            } else {
                self.neighbors[right].push((left, weight));
            }
        }
    }
    fn edges(&self) -> Vec<(usize, usize, f64)> {
        self.neighbors
            .iter()
            .enumerate()
            .flat_map(|(left, neighbors)| {
                neighbors
                    .iter()
                    .filter(move |(right, _)| *right >= left)
                    .map(move |(right, weight)| (left, *right, *weight))
            })
            .collect()
    }
    fn degrees(&self) -> Vec<f64> {
        self.neighbors
            .iter()
            .enumerate()
            .map(|(node, neighbors)| {
                neighbors
                    .iter()
                    .map(|(other, weight)| {
                        if node == *other {
                            2.0 * weight
                        } else {
                            *weight
                        }
                    })
                    .sum()
            })
            .collect()
    }
    fn modularity(&self, parts: &[BTreeSet<usize>], resolution: f64) -> f64 {
        let degrees = self.degrees();
        let degree_sum = degrees.iter().sum::<f64>();
        let m = degree_sum / 2.0;
        let norm = 1.0 / degree_sum.powi(2);
        parts
            .iter()
            .map(|part| {
                let sum = part.iter().map(|node| degrees[*node]).sum::<f64>();
                let internal = part
                    .iter()
                    .flat_map(|node| {
                        self.neighbors[*node]
                            .iter()
                            .filter(move |(other, _)| part.contains(other) && *other >= *node)
                            .map(|(_, weight)| *weight)
                    })
                    .sum::<f64>();
                internal / m - resolution * sum * sum * norm
            })
            .sum()
    }
}
fn level(
    graph: &Graph,
    m: f64,
    mut partition: Vec<BTreeSet<usize>>,
    resolution: f64,
    random: &mut PythonRandom,
) -> (Vec<BTreeSet<usize>>, Vec<BTreeSet<usize>>, bool) {
    let mut owners = (0..graph.nodes.len()).collect::<Vec<_>>();
    let mut inner = (0..graph.nodes.len())
        .map(|node| BTreeSet::from([node]))
        .collect::<Vec<_>>();
    let degrees = graph.degrees();
    let mut total = degrees.clone();
    let mut order = (0..graph.nodes.len()).collect::<Vec<_>>();
    random.shuffle(&mut order);
    let mut improvement = false;
    loop {
        let mut moves = 0;
        for node in &order {
            let node = *node;
            let mut best_gain = 0.0;
            let mut best = owners[node];
            let mut weights: Vec<(usize, f64)> = Vec::new();
            for (neighbor, weight) in &graph.neighbors[node] {
                if *neighbor == node {
                    continue;
                }
                let owner = owners[*neighbor];
                if let Some((_, sum)) = weights.iter_mut().find(|(group, _)| *group == owner) {
                    *sum += *weight;
                } else {
                    weights.push((owner, *weight));
                }
            }
            total[best] -= degrees[node];
            let own_weight =
                if let Some((_, weight)) = weights.iter().find(|(group, _)| *group == best) {
                    *weight
                } else {
                    weights.push((best, 0.0));
                    0.0
                };
            let remove =
                -own_weight / m + resolution * (total[best] * degrees[node]) / (2.0 * m.powi(2));
            for (community, weight) in weights {
                let gain = remove + weight / m
                    - resolution * (total[community] * degrees[node]) / (2.0 * m.powi(2));
                if gain > best_gain {
                    best_gain = gain;
                    best = community;
                }
            }
            total[best] += degrees[node];
            if best != owners[node] {
                let old = owners[node];
                for original in &graph.nodes[node] {
                    partition[old].remove(original);
                    partition[best].insert(*original);
                }
                inner[old].remove(&node);
                inner[best].insert(node);
                owners[node] = best;
                improvement = true;
                moves += 1;
            }
        }
        if moves == 0 {
            break;
        }
    }
    (
        partition
            .into_iter()
            .filter(|part| !part.is_empty())
            .collect(),
        inner.into_iter().filter(|part| !part.is_empty()).collect(),
        improvement,
    )
}
fn aggregate(graph: &Graph, parts: &[BTreeSet<usize>]) -> Graph {
    let mut owners = vec![0; graph.nodes.len()];
    let nodes = parts
        .iter()
        .enumerate()
        .map(|(index, part)| {
            let mut members = BTreeSet::new();
            for node in part {
                owners[*node] = index;
                members.extend(&graph.nodes[*node]);
            }
            members
        })
        .collect();
    let mut result = Graph::new(nodes);
    for (left, right, weight) in graph.edges() {
        result.edge(owners[left], owners[right], weight);
    }
    result
}
fn communities(
    base: &Graph,
    selected: &BTreeSet<usize>,
    resolution: f64,
    seed: &str,
) -> Vec<Vec<usize>> {
    let mapping = selected
        .iter()
        .enumerate()
        .map(|(index, node)| (*node, index))
        .collect::<BTreeMap<_, _>>();
    let mut graph = Graph::new(
        selected
            .iter()
            .map(|node| BTreeSet::from([*node]))
            .collect(),
    );
    for (left, right, weight) in base.edges() {
        if let (Some(left), Some(right)) = (mapping.get(&left), mapping.get(&right)) {
            graph.edge(*left, *right, weight);
        }
    }
    if graph.edges().is_empty() {
        return selected.iter().map(|node| vec![*node]).collect();
    }
    let mut partition = graph.nodes.clone();
    let mut modularity = graph.modularity(
        &(0..graph.nodes.len())
            .map(|node| BTreeSet::from([node]))
            .collect::<Vec<_>>(),
        resolution,
    );
    let m = graph.degrees().iter().sum::<f64>() / 2.0;
    let mut random = PythonRandom::new(seed);
    loop {
        let (next, inner, improvement) = level(&graph, m, partition, resolution, &mut random);
        partition = next;
        let next_modularity = graph.modularity(&inner, resolution);
        if !improvement || next_modularity - modularity <= 0.0000001 {
            break;
        }
        modularity = next_modularity;
        graph = aggregate(&graph, &inner);
    }
    let mut result = Vec::new();
    for part in partition {
        let mut remaining = part.clone();
        while let Some(first) = remaining.pop_first() {
            let mut component = BTreeSet::from([first]);
            let mut stack = vec![first];
            while let Some(node) = stack.pop() {
                for (neighbor, _) in &base.neighbors[node] {
                    if part.contains(neighbor) && remaining.remove(neighbor) {
                        component.insert(*neighbor);
                        stack.push(*neighbor);
                    }
                }
            }
            result.push(component.into_iter().collect::<Vec<_>>());
        }
    }
    result.sort();
    result
}
fn rounded(value: f64) -> f64 {
    format!("{value:.6}").parse().expect("finite similarity")
}
pub fn group_vectors(vectors: &BTreeMap<String, Vec<f32>>, parameters: &Value) -> Result<Value> {
    validate_parameters(parameters)?;
    let identities = vectors.keys().cloned().collect::<Vec<_>>();
    let count = identities.len();
    let mut graph = Graph::new((0..count).map(|node| BTreeSet::from([node])).collect());
    let neighbors = parameters["neighbors"].as_u64().unwrap() as usize;
    let threshold = number(&parameters["similarity"]).unwrap();
    let dimension = vectors.values().next().map(Vec::len).unwrap_or(0);
    let mut normalized = Vec::new();
    for vector in vectors.values() {
        require(
            vector.len() == dimension && vector.iter().all(|v| v.is_finite()),
            "INVALID_VECTOR",
        )?;
        let norm = vector
            .iter()
            .map(|v| f64::from(*v).powi(2))
            .sum::<f64>()
            .sqrt();
        require(norm > 0.0, "INVALID_VECTOR")?;
        normalized.push(
            vector
                .iter()
                .map(|v| f64::from(*v) / norm)
                .collect::<Vec<_>>(),
        );
    }
    let mut edges = BTreeMap::new();
    for left in 0..count {
        let mut distances = (0..count)
            .map(|right| {
                let similarity = normalized[left]
                    .iter()
                    .zip(&normalized[right])
                    .map(|(a, b)| a * b)
                    .sum::<f64>()
                    .clamp(-1.0, 1.0);
                (1.0 - similarity, right)
            })
            .collect::<Vec<_>>();
        distances.sort_by(|a, b| {
            a.0.total_cmp(&b.0)
                .then_with(|| identities[a.1].cmp(&identities[b.1]))
        });
        distances.truncate(count.min(neighbors + 1));
        distances.sort_by(|a, b| {
            rounded(a.0)
                .total_cmp(&rounded(b.0))
                .then_with(|| identities[a.1].cmp(&identities[b.1]))
        });
        for (distance, right) in distances {
            require(
                distance.is_finite() && (-0.000001..=2.000001).contains(&distance),
                "INVALID_SIMILARITY",
            )?;
            let weight = rounded((1.0 - distance).clamp(-1.0, 1.0));
            if left != right && weight >= threshold {
                edges.insert((left.min(right), left.max(right)), weight);
            }
        }
    }
    for ((left, right), weight) in &edges {
        graph.edge(*left, *right, *weight);
    }
    let seed = parameters["seed"].to_string();
    let all = (0..count).collect::<BTreeSet<_>>();
    let parts = communities(
        &graph,
        &all,
        number(&parameters["area_resolution"]).unwrap(),
        &seed,
    );
    let singleton = parts.iter().filter(|members| members.len() == 1).count();
    let mut areas = Vec::new();
    for members in parts {
        let selected = members.iter().copied().collect::<BTreeSet<_>>();
        let works = communities(
            &graph,
            &selected,
            number(&parameters["work_resolution"]).unwrap(),
            &seed,
        );
        let members = members
            .into_iter()
            .map(|node| identities[node].clone())
            .collect::<Vec<_>>();
        areas.push(json!({"id":digest(&json!(["area",members])),"members":members,"work_groups":works.into_iter().map(|work|{let members=work.into_iter().map(|node|identities[node].clone()).collect::<Vec<_>>();json!({"id":digest(&json!(["work",members])),"members":members})}).collect::<Vec<_>>()}));
    }
    Ok(
        json!({"engine":{"method":GROUPING_METHOD,"implementation":"localbrain-rust","version":1,"numeric":"f64-cosine-over-cached-f32-v1","rng":"python-mt19937-integer-seed-v1"},"authority":"inferred-affinity-only","areas":areas,"node_count":count,"edge_count":edges.len(),"singleton_areas":singleton,"edges":edges.into_iter().map(|((left,right),weight)|json!({"left":identities[left],"right":identities[right],"similarity":weight})).collect::<Vec<_>>()}),
    )
}
