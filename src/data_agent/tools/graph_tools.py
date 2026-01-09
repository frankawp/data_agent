"""
图分析工具

使用networkx进行图算法和网络分析。
"""

import json
import logging
from typing import List, Tuple, Optional, Dict, Any

import networkx as nx
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# 存储创建的图
_graph_store: Dict[str, nx.Graph] = {}


@tool
def create_graph(
    edges_json: str,
    directed: bool = False,
    graph_id: Optional[str] = None
) -> str:
    """
    创建图结构

    Args:
        edges_json: JSON格式的边列表，每条边是[source, target]或[source, target, weight]
        directed: 是否为有向图，默认False
        graph_id: 图ID，用于保存和后续引用

    Returns:
        图的基本信息

    示例:
        create_graph(
            edges_json='[["A", "B"], ["B", "C"], ["A", "C"]]',
            directed=False,
            graph_id="my_graph"
        )
    """
    try:
        edges = json.loads(edges_json)

        if directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        for edge in edges:
            if len(edge) == 2:
                G.add_edge(edge[0], edge[1])
            elif len(edge) >= 3:
                G.add_edge(edge[0], edge[1], weight=edge[2])

        # 保存图
        if graph_id:
            _graph_store[graph_id] = G

        result = f"图创建成功\n"
        result += f"类型: {'有向图' if directed else '无向图'}\n"
        result += f"节点数: {G.number_of_nodes()}\n"
        result += f"边数: {G.number_of_edges()}\n"
        result += f"节点列表: {list(G.nodes())[:20]}{'...' if G.number_of_nodes() > 20 else ''}"

        if graph_id:
            result += f"\n图已保存，ID: {graph_id}"

        return result

    except Exception as e:
        logger.error(f"创建图错误: {e}")
        return f"创建图失败: {str(e)}"


@tool
def graph_analysis(graph_id: str, algorithm: str) -> str:
    """
    执行图算法分析

    Args:
        graph_id: 图ID
        algorithm: 算法名称，支持:
                  - degree: 度分布
                  - centrality: 中心性分析
                  - clustering: 聚类系数
                  - components: 连通分量
                  - shortest_path: 最短路径（需要指定起点终点）
                  - pagerank: PageRank算法
                  - community: 社区发现
                  - density: 图密度

    Returns:
        分析结果

    示例:
        graph_analysis("my_graph", "centrality")
    """
    if graph_id not in _graph_store:
        return f"图不存在: {graph_id}"

    G = _graph_store[graph_id]
    algorithm = algorithm.lower()

    try:
        if algorithm == "degree":
            degrees = dict(G.degree())
            sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
            result = f"度分布分析:\n"
            result += f"平均度: {sum(degrees.values()) / len(degrees):.2f}\n"
            result += f"最大度: {max(degrees.values())}\n"
            result += f"最小度: {min(degrees.values())}\n"
            result += f"\n度排名前10:\n"
            for node, degree in sorted_degrees[:10]:
                result += f"  {node}: {degree}\n"
            return result

        elif algorithm == "centrality":
            # 度中心性
            degree_cent = nx.degree_centrality(G)
            # 介数中心性
            betweenness_cent = nx.betweenness_centrality(G)
            # 接近中心性
            try:
                closeness_cent = nx.closeness_centrality(G)
            except:
                closeness_cent = {}

            result = f"中心性分析:\n"
            result += f"\n度中心性 Top 5:\n"
            for node, cent in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
                result += f"  {node}: {cent:.4f}\n"

            result += f"\n介数中心性 Top 5:\n"
            for node, cent in sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
                result += f"  {node}: {cent:.4f}\n"

            if closeness_cent:
                result += f"\n接近中心性 Top 5:\n"
                for node, cent in sorted(closeness_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
                    result += f"  {node}: {cent:.4f}\n"

            return result

        elif algorithm == "clustering":
            if isinstance(G, nx.DiGraph):
                return "聚类系数不适用于有向图"

            clustering = nx.clustering(G)
            avg_clustering = nx.average_clustering(G)

            result = f"聚类系数分析:\n"
            result += f"平均聚类系数: {avg_clustering:.4f}\n"
            result += f"\n节点聚类系数 Top 10:\n"
            for node, coef in sorted(clustering.items(), key=lambda x: x[1], reverse=True)[:10]:
                result += f"  {node}: {coef:.4f}\n"
            return result

        elif algorithm == "components":
            if isinstance(G, nx.DiGraph):
                # 有向图使用强连通分量
                components = list(nx.strongly_connected_components(G))
                comp_type = "强连通分量"
            else:
                components = list(nx.connected_components(G))
                comp_type = "连通分量"

            result = f"{comp_type}分析:\n"
            result += f"分量数: {len(components)}\n"
            result += f"\n各分量大小:\n"
            for i, comp in enumerate(sorted(components, key=len, reverse=True)[:10]):
                result += f"  分量{i+1}: {len(comp)}个节点\n"
            return result

        elif algorithm == "pagerank":
            if not isinstance(G, nx.DiGraph):
                G = G.to_directed()

            pr = nx.pagerank(G)
            result = f"PageRank分析:\n"
            result += f"\nPageRank Top 10:\n"
            for node, score in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:10]:
                result += f"  {node}: {score:.6f}\n"
            return result

        elif algorithm == "community":
            try:
                from networkx.algorithms import community
                # 使用Louvain算法
                communities = community.louvain_communities(G)

                result = f"社区发现分析 (Louvain):\n"
                result += f"社区数: {len(communities)}\n"
                result += f"\n各社区大小:\n"
                for i, comm in enumerate(sorted(communities, key=len, reverse=True)[:10]):
                    result += f"  社区{i+1}: {len(comm)}个节点\n"
                return result
            except Exception as e:
                return f"社区发现失败: {str(e)}"

        elif algorithm == "density":
            density = nx.density(G)
            result = f"图密度分析:\n"
            result += f"密度: {density:.6f}\n"
            result += f"说明: 密度范围[0,1]，1表示完全图"
            return result

        else:
            return f"未知的算法: {algorithm}"

    except Exception as e:
        logger.error(f"图分析错误: {e}")
        return f"分析失败: {str(e)}"


@tool
def shortest_path(graph_id: str, source: str, target: str) -> str:
    """
    计算两节点间的最短路径

    Args:
        graph_id: 图ID
        source: 起点
        target: 终点

    Returns:
        最短路径信息
    """
    if graph_id not in _graph_store:
        return f"图不存在: {graph_id}"

    G = _graph_store[graph_id]

    try:
        if source not in G:
            return f"起点不存在: {source}"
        if target not in G:
            return f"终点不存在: {target}"

        path = nx.shortest_path(G, source, target)
        path_length = nx.shortest_path_length(G, source, target)

        result = f"最短路径分析:\n"
        result += f"起点: {source}\n"
        result += f"终点: {target}\n"
        result += f"路径长度: {path_length}\n"
        result += f"路径: {' -> '.join(map(str, path))}"
        return result

    except nx.NetworkXNoPath:
        return f"从 {source} 到 {target} 不存在路径"
    except Exception as e:
        logger.error(f"最短路径计算错误: {e}")
        return f"计算失败: {str(e)}"


@tool
def list_graphs() -> str:
    """
    列出所有已创建的图

    Returns:
        图列表
    """
    if not _graph_store:
        return "没有已创建的图"

    result = "已创建的图:\n"
    for graph_id, G in _graph_store.items():
        graph_type = "有向图" if isinstance(G, nx.DiGraph) else "无向图"
        result += f"- {graph_id}: {graph_type}, {G.number_of_nodes()}节点, {G.number_of_edges()}边\n"

    return result


@tool
def graph_to_json(graph_id: str) -> str:
    """
    将图导出为JSON格式

    Args:
        graph_id: 图ID

    Returns:
        JSON格式的图数据
    """
    if graph_id not in _graph_store:
        return f"图不存在: {graph_id}"

    G = _graph_store[graph_id]

    data = {
        "nodes": list(G.nodes()),
        "edges": list(G.edges(data=True)),
        "directed": isinstance(G, nx.DiGraph)
    }

    return json.dumps(data, indent=2, default=str)
