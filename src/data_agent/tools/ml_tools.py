"""
机器学习工具

使用scikit-learn进行分类、回归、聚类等任务。
"""

import json
import logging
import pickle
from typing import Optional, Dict, Any
from io import BytesIO
import base64

import numpy as np
import pandas as pd
from langchain_core.tools import tool
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score,
    silhouette_score
)

logger = logging.getLogger(__name__)

# 存储训练好的模型
_model_store: Dict[str, Any] = {}


def _get_model_by_type(model_type: str):
    """根据类型获取模型类"""
    from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge, Lasso
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.svm import SVC, SVR
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.naive_bayes import GaussianNB

    models = {
        # 分类
        "logistic_regression": LogisticRegression,
        "decision_tree_classifier": DecisionTreeClassifier,
        "random_forest_classifier": RandomForestClassifier,
        "svc": SVC,
        "knn_classifier": KNeighborsClassifier,
        "naive_bayes": GaussianNB,

        # 回归
        "linear_regression": LinearRegression,
        "ridge": Ridge,
        "lasso": Lasso,
        "decision_tree_regressor": DecisionTreeRegressor,
        "random_forest_regressor": RandomForestRegressor,
        "svr": SVR,
        "knn_regressor": KNeighborsRegressor,

        # 聚类
        "kmeans": KMeans,
        "dbscan": DBSCAN,
    }

    return models.get(model_type.lower())


@tool
def train_model(
    data_json: str,
    target_column: str,
    model_type: str,
    feature_columns: Optional[str] = None,
    test_size: float = 0.2,
    model_id: Optional[str] = None
) -> str:
    """
    训练机器学习模型

    Args:
        data_json: JSON格式的训练数据
        target_column: 目标列名
        model_type: 模型类型，支持:
                   分类: logistic_regression, decision_tree_classifier,
                        random_forest_classifier, svc, knn_classifier, naive_bayes
                   回归: linear_regression, ridge, lasso,
                        decision_tree_regressor, random_forest_regressor,
                        svr, knn_regressor
                   聚类: kmeans, dbscan
        feature_columns: 特征列名（逗号分隔），默认使用除目标列外的所有数值列
        test_size: 测试集比例，默认0.2
        model_id: 模型ID，用于保存和后续引用

    Returns:
        训练结果和模型评估指标

    示例:
        train_model(
            data_json='[{"feature1": 1, "feature2": 2, "target": 0}, ...]',
            target_column="target",
            model_type="random_forest_classifier",
            model_id="my_model"
        )
    """
    try:
        # 解析数据
        data = json.loads(data_json)
        df = pd.DataFrame(data)

        # 确定特征列
        if feature_columns:
            features = [col.strip() for col in feature_columns.split(",")]
        else:
            features = [col for col in df.columns if col != target_column]
            features = df[features].select_dtypes(include=[np.number]).columns.tolist()

        X = df[features].values
        y = df[target_column].values

        # 检查是否需要编码标签
        if y.dtype == object:
            le = LabelEncoder()
            y = le.fit_transform(y)
        else:
            le = None

        # 获取模型
        model_class = _get_model_by_type(model_type)
        if model_class is None:
            return f"不支持的模型类型: {model_type}"

        # 聚类模型特殊处理
        if model_type.lower() in ["kmeans", "dbscan"]:
            model = model_class()
            model.fit(X)

            if model_type.lower() == "kmeans":
                labels = model.labels_
                score = silhouette_score(X, labels)
                result = f"聚类模型训练完成\n"
                result += f"模型类型: {model_type}\n"
                result += f"聚类数: {len(set(labels))}\n"
                result += f"轮廓系数: {score:.4f}"
            else:
                labels = model.labels_
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                result = f"聚类模型训练完成\n"
                result += f"模型类型: {model_type}\n"
                result += f"聚类数: {n_clusters}\n"
                result += f"噪声点数: {list(labels).count(-1)}"

        else:
            # 分类/回归模型
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # 标准化
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            # 训练
            model = model_class()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # 评估
            if model_type.lower() in ["logistic_regression", "decision_tree_classifier",
                                       "random_forest_classifier", "svc",
                                       "knn_classifier", "naive_bayes"]:
                # 分类指标
                acc = accuracy_score(y_test, y_pred)
                prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
                rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
                f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)

                result = f"分类模型训练完成\n"
                result += f"模型类型: {model_type}\n"
                result += f"特征数: {len(features)}\n"
                result += f"训练样本数: {len(X_train)}\n"
                result += f"测试样本数: {len(X_test)}\n"
                result += f"\n评估指标:\n"
                result += f"- 准确率: {acc:.4f}\n"
                result += f"- 精确率: {prec:.4f}\n"
                result += f"- 召回率: {rec:.4f}\n"
                result += f"- F1分数: {f1:.4f}"
            else:
                # 回归指标
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                result = f"回归模型训练完成\n"
                result += f"模型类型: {model_type}\n"
                result += f"特征数: {len(features)}\n"
                result += f"训练样本数: {len(X_train)}\n"
                result += f"测试样本数: {len(X_test)}\n"
                result += f"\n评估指标:\n"
                result += f"- MSE: {mse:.4f}\n"
                result += f"- MAE: {mae:.4f}\n"
                result += f"- R²: {r2:.4f}"

            # 保存scaler
            model._scaler = scaler

        # 保存模型
        if model_id:
            _model_store[model_id] = {
                "model": model,
                "features": features,
                "label_encoder": le,
                "model_type": model_type
            }
            result += f"\n\n模型已保存，ID: {model_id}"

        return result

    except Exception as e:
        logger.error(f"模型训练错误: {e}")
        return f"训练失败: {str(e)}"


@tool
def predict(model_id: str, data_json: str) -> str:
    """
    使用训练好的模型进行预测

    Args:
        model_id: 模型ID
        data_json: JSON格式的预测数据

    Returns:
        预测结果

    示例:
        predict(
            model_id="my_model",
            data_json='[{"feature1": 1, "feature2": 2}, {"feature1": 3, "feature2": 4}]'
        )
    """
    if model_id not in _model_store:
        return f"模型不存在: {model_id}"

    try:
        model_info = _model_store[model_id]
        model = model_info["model"]
        features = model_info["features"]
        le = model_info.get("label_encoder")

        # 解析数据
        data = json.loads(data_json)
        df = pd.DataFrame(data)

        # 确保特征列存在
        missing_cols = [col for col in features if col not in df.columns]
        if missing_cols:
            return f"缺少特征列: {missing_cols}"

        X = df[features].values

        # 标准化（如果模型有scaler）
        if hasattr(model, "_scaler"):
            X = model._scaler.transform(X)

        # 预测
        predictions = model.predict(X)

        # 反向编码标签
        if le is not None:
            predictions = le.inverse_transform(predictions)

        # 构建结果
        result_df = df.copy()
        result_df["prediction"] = predictions

        return f"预测结果:\n{result_df.to_string()}"

    except Exception as e:
        logger.error(f"预测错误: {e}")
        return f"预测失败: {str(e)}"


@tool
def evaluate_model(model_id: str, data_json: str, target_column: str) -> str:
    """
    评估模型在新数据上的表现

    Args:
        model_id: 模型ID
        data_json: JSON格式的测试数据
        target_column: 目标列名

    Returns:
        评估结果
    """
    if model_id not in _model_store:
        return f"模型不存在: {model_id}"

    try:
        model_info = _model_store[model_id]
        model = model_info["model"]
        features = model_info["features"]
        le = model_info.get("label_encoder")
        model_type = model_info["model_type"]

        # 解析数据
        data = json.loads(data_json)
        df = pd.DataFrame(data)

        X = df[features].values
        y = df[target_column].values

        # 编码标签
        if le is not None:
            y = le.transform(y)

        # 标准化
        if hasattr(model, "_scaler"):
            X = model._scaler.transform(X)

        # 预测
        y_pred = model.predict(X)

        # 计算指标
        if model_type.lower() in ["logistic_regression", "decision_tree_classifier",
                                   "random_forest_classifier", "svc",
                                   "knn_classifier", "naive_bayes"]:
            acc = accuracy_score(y, y_pred)
            prec = precision_score(y, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y, y_pred, average="weighted", zero_division=0)

            result = f"模型评估结果 ({model_id}):\n"
            result += f"样本数: {len(y)}\n"
            result += f"- 准确率: {acc:.4f}\n"
            result += f"- 精确率: {prec:.4f}\n"
            result += f"- 召回率: {rec:.4f}\n"
            result += f"- F1分数: {f1:.4f}"
        else:
            mse = mean_squared_error(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            r2 = r2_score(y, y_pred)

            result = f"模型评估结果 ({model_id}):\n"
            result += f"样本数: {len(y)}\n"
            result += f"- MSE: {mse:.4f}\n"
            result += f"- MAE: {mae:.4f}\n"
            result += f"- R²: {r2:.4f}"

        return result

    except Exception as e:
        logger.error(f"模型评估错误: {e}")
        return f"评估失败: {str(e)}"


@tool
def list_models() -> str:
    """
    列出所有已训练的模型

    Returns:
        模型列表
    """
    if not _model_store:
        return "没有已训练的模型"

    result = "已训练的模型:\n"
    for model_id, info in _model_store.items():
        result += f"- {model_id}: {info['model_type']}, 特征数: {len(info['features'])}\n"

    return result


@tool
def feature_importance(model_id: str) -> str:
    """
    获取模型的特征重要性

    仅支持树模型（决策树、随机森林）

    Args:
        model_id: 模型ID

    Returns:
        特征重要性排名
    """
    if model_id not in _model_store:
        return f"模型不存在: {model_id}"

    model_info = _model_store[model_id]
    model = model_info["model"]
    features = model_info["features"]

    if not hasattr(model, "feature_importances_"):
        return "该模型不支持特征重要性分析"

    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        "feature": features,
        "importance": importances
    }).sort_values("importance", ascending=False)

    return f"特征重要性:\n{importance_df.to_string(index=False)}"
