"""图分析工具（networkx）"""

import json
import networkx as nx
from typing import Optional, Dict, Any, List
from langchain_core.tools import StructuredTool


def analyze_graph(
    operation: str,
    graph_data: str,
    params: Optional[str] = None
) -> str:
    """执行图分析操作

    Args:
        operation: 分析类型
                   - basic_stats: 基本统计信息
                   - shortest_path: 最短路径
                   - centrality: 中心性分析
                   - community: 社区发现
                   - connected_components: 连通分量
                   - pagerank: PageRank算法
        graph_data: 图数据（JSON格式，边列表或邻接表）
        params: 操作参数（JSON格式）

    Returns:
        分析结果（JSON格式）
    """
    try:
        # 解析参数
        params_dict = json.loads(params) if params else {}

        # 创建图
        graph_format = params_dict.get('format', 'edges')  # edges或adjacency
        directed = params_dict.get('directed', False)

        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # 读取图数据
        data_dict = json.loads(graph_data)

        if graph_format == 'edges':
            # 边列表格式: [["node1", "node2"], ["node2", "node3"], ...]
            for edge in data_dict:
                if len(edge) >= 2:
                    if len(edge) == 3:
                        G.add_edge(edge[0], edge[1], weight=edge[2])
                    else:
                        G.add_edge(edge[0], edge[1])
        elif graph_format == 'adjacency':
            # 邻接表格式: {"node1": ["node2", "node3"], ...}
            for node, neighbors in data_dict.items():
                for neighbor in neighbors:
                    G.add_edge(node, neighbor)

        result = {
            "success": True,
            "operation": operation
        }

        if operation == "basic_stats":
            # 基本统计信息
            result["stats"] = {
                "nodes": G.number_of_nodes(),
                "edges": G.number_of_edges(),
                "is_directed": G.is_directed(),
                "density": float(nx.density(G)),
                "avg_degree": float(sum(dict(G.degree()).values()) / G.number_of_nodes()) if G.number_of_nodes() > 0 else 0
            }

            if G.is_directed():
                result["stats"]["is_weakly_connected"] = nx.is_weakly_connected(G)
                result["stats"]["is_strongly_connected"] = nx.is_strongly_connected(G)
            else:
                result["stats"]["is_connected"] = nx.is_connected(G)

        elif operation == "shortest_path":
            # 最短路径
            source = params_dict.get('source')
            target = params_dict.get('target')

            if not source or not target:
                return json.dumps({
                    "success": False,
                    "error": "请指定source和target参数"
                }, ensure_ascii=False)

            if source not in G.nodes() or target not in G.nodes():
                return json.dumps({
                    "success": False,
                    "error": "指定的节点不存在"
                }, ensure_ascii=False)

            try:
                path = nx.shortest_path(G, source=source, target=target)
                path_length = nx.shortest_path_length(G, source=source, target=target)

                result["shortest_path"] = {
                    "source": source,
                    "target": target,
                    "path": path,
                    "length": path_length
                }
            except nx.NetworkXNoPath:
                result["shortest_path"] = {
                    "source": source,
                    "target": target,
                    "error": "两节点之间不存在路径"
                }

        elif operation == "centrality":
            # 中心性分析
            centrality_type = params_dict.get('type', 'degree')  # degree, betweenness, closeness, eigenvector

            if centrality_type == 'degree':
                centrality = nx.degree_centrality(G)
            elif centrality_type == 'betweenness':
                centrality = nx.betweenness_centrality(G)
            elif centrality_type == 'closeness':
                centrality = nx.closeness_centrality(G)
            elif centrality_type == 'eigenvector':
                try:
                    centrality = nx.eigenvector_centrality(G, max_iter=1000)
                except:
                    centrality = {}
            elif centrality_type == 'pagerank':
                centrality = nx.pagerank(G)
            else:
                return json.dumps({
                    "success": False,
                    "error": f"未知的中心性类型: {centrality_type}"
                }, ensure_ascii=False)

            # 排序并返回top节点
            sorted_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            result["centrality"] = {
                "type": centrality_type,
                "top_nodes": [
                    {"node": node, "value": float(value)}
                    for node, value in sorted_centrality[:10]
                ]
            }

        elif operation == "community":
            # 社区发现
            algorithm = params_dict.get('algorithm', 'greedy')  # greedy, label_propagation

            if algorithm == 'greedy':
                communities = list(nx.community.greedy_modularity_communities(G))
                modularity = nx.community.modularity(G, communities)
            elif algorithm == 'label_propagation':
                communities = list(nx.community.label_propagation_communities(G))
                modularity = None
            else:
                return json.dumps({
                    "success": False,
                    "error": f"未知的社区发现算法: {algorithm}"
                }, ensure_ascii=False)

            result["communities"] = {
                "algorithm": algorithm,
                "count": len(communities),
                "modularity": float(modularity) if modularity else None,
                "communities": [list(community) for community in communities]
            }

        elif operation == "connected_components":
            # 连通分量
            if G.is_directed():
                # 有向图
                weak_components = list(nx.weakly_connected_components(G))
                strong_components = list(nx.strongly_connected_components(G))

                result["connected_components"] = {
                    "weakly_connected_components": len(weak_components),
                    "strongly_connected_components": len(strong_components),
                    "largest_weak_component_size": max(len(c) for c in weak_components) if weak_components else 0,
                    "largest_strong_component_size": max(len(c) for c in strong_components) if strong_components else 0
                }
            else:
                # 无向图
                components = list(nx.connected_components(G))

                result["connected_components"] = {
                    "count": len(components),
                    "largest_component_size": max(len(c) for c in components) if components else 0
                }

        elif operation == "pagerank":
            # PageRank
            alpha = params_dict.get('alpha', 0.85)
            max_iter = params_dict.get('max_iter', 100)

            pagerank = nx.pagerank(G, alpha=alpha, max_iter=max_iter)
            sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)

            result["pagerank"] = {
                "top_nodes": [
                    {"node": node, "rank": float(rank)}
                    for node, rank in sorted_pagerank[:10]
                ]
            }

        else:
            result["error"] = f"未知的操作类型: {operation}"

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


def create_graph(
    nodes: Optional[List[str]] = None,
    edges: Optional[List[List[str]]] = None,
    directed: bool = False
) -> str:
    """创建图结构

    Args:
        nodes: 节点列表
        edges: 边列表
        directed: 是否为有向图

    Returns:
        图的统计信息（JSON格式）
    """
    try:
        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        if nodes:
            G.add_nodes_from(nodes)

        if edges:
            G.add_edges_from(edges)

        return json.dumps({
            "success": True,
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "is_directed": G.is_directed(),
            "graph": nx.node_link_data(G)
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


# 创建LangChain工具
graph_analyze_tool = StructuredTool.from_function(
    func=analyze_graph,
    name="graph_analyze",
    description="执行图分析操作。支持基本统计、最短路径、中心性分析、社区发现、连通分量、PageRank。参数: operation（操作类型）, graph_data（图数据JSON）, params（参数JSON）"
)

graph_create_tool = StructuredTool.from_function(
    func=create_graph,
    name="graph_create",
    description="创建图结构。参数: nodes（节点列表）, edges（边列表）, directed（是否有向图）"
)

# 导出所有工具
GRAPH_TOOLS = [graph_analyze_tool, graph_create_tool]
