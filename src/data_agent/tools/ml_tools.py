"""机器学习工具（sklearn）"""

import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.svm import SVC, SVR
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, silhouette_score
from typing import Optional, Dict, Any
from langchain_core.tools import StructuredTool


def train_model(
    algorithm: str,
    training_data: str,
    target_column: str,
    params: Optional[str] = None
) -> str:
    """训练机器学习模型

    Args:
        algorithm: 算法类型
                   - linear_regression: 线性回归
                   - logistic_regression: 逻辑回归
                   - random_forest_classifier: 随机森林分类
                   - random_forest_regressor: 随机森林回归
                   - svm_classifier: SVM分类
                   - svm_regressor: SVM回归
                   - kmeans: K-Means聚类
        training_data: 训练数据（JSON格式）
        target_column: 目标列名
        params: 模型参数（JSON格式）

    Returns:
        训练结果（JSON格式）
    """
    try:
        # 解析参数
        params_dict = json.loads(params) if params else {}

        # 读取数据
        df = pd.read_json(training_data)

        # 分离特征和目标
        if target_column not in df.columns:
            return json.dumps({
                "success": False,
                "error": f"目标列 {target_column} 不存在"
            }, ensure_ascii=False)

        X = df.drop(columns=[target_column])
        y = df[target_column]

        # 划分训练集和测试集
        test_size = params_dict.get('test_size', 0.2)
        random_state = params_dict.get('random_state', 42)

        if algorithm != 'kmeans':  # 聚类不需要划分
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

        # 选择并训练模型
        if algorithm == 'linear_regression':
            model = LinearRegression()
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'mse': float(mean_squared_error(y_test, predictions)),
                'r2': float(r2_score(y_test, predictions)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, predictions)))
            }

            if hasattr(model, 'coef_'):
                metrics['coefficients'] = model.coef_.tolist()
            if hasattr(model, 'intercept_'):
                metrics['intercept'] = float(model.intercept_)

        elif algorithm == 'logistic_regression':
            max_iter = params_dict.get('max_iter', 1000)
            model = LogisticRegression(max_iter=max_iter, random_state=random_state)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'accuracy': float(accuracy_score(y_test, predictions))
            }

        elif algorithm == 'random_forest_classifier':
            n_estimators = params_dict.get('n_estimators', 100)
            max_depth = params_dict.get('max_depth', None)

            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state
            )
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'accuracy': float(accuracy_score(y_test, predictions))
            }

            if hasattr(model, 'feature_importances_'):
                metrics['feature_importance'] = {
                    col: float(importance)
                    for col, importance in zip(X.columns, model.feature_importances_)
                }

        elif algorithm == 'random_forest_regressor':
            n_estimators = params_dict.get('n_estimators', 100)
            max_depth = params_dict.get('max_depth', None)

            model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state
            )
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'mse': float(mean_squared_error(y_test, predictions)),
                'r2': float(r2_score(y_test, predictions)),
                'rmse': float(np.sqrt(mean_squared_error(y_test, predictions)))
            }

            if hasattr(model, 'feature_importances_'):
                metrics['feature_importance'] = {
                    col: float(importance)
                    for col, importance in zip(X.columns, model.feature_importances_)
                }

        elif algorithm == 'svm_classifier':
            C = params_dict.get('C', 1.0)
            kernel = params_dict.get('kernel', 'rbf')

            model = SVC(C=C, kernel=kernel, random_state=random_state)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'accuracy': float(accuracy_score(y_test, predictions))
            }

        elif algorithm == 'svm_regressor':
            C = params_dict.get('C', 1.0)
            kernel = params_dict.get('kernel', 'rbf')

            model = SVR(C=C, kernel=kernel)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)

            metrics = {
                'mse': float(mean_squared_error(y_test, predictions)),
                'r2': float(r2_score(y_test, predictions))
            }

        elif algorithm == 'kmeans':
            n_clusters = params_dict.get('n_clusters', 3)
            max_iter = params_dict.get('max_iter', 300)

            model = KMeans(n_clusters=n_clusters, max_iter=max_iter, random_state=random_state)
            model.fit(X)
            predictions = model.predict(X)

            metrics = {
                'inertia': float(model.inertia_),
                'n_clusters': n_clusters
            }

            # 计算轮廓系数
            if len(X) > n_clusters:
                metrics['silhouette_score'] = float(silhouette_score(X, predictions))

        else:
            return json.dumps({
                "success": False,
                "error": f"未知的算法类型: {algorithm}"
            }, ensure_ascii=False)

        return json.dumps({
            "success": True,
            "model_type": algorithm,
            "target_column": target_column,
            "metrics": metrics,
            "training_samples": len(X_train) if algorithm != 'kmeans' else len(X),
            "test_samples": len(X_test) if algorithm != 'kmeans' else 0
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


def predict_model(
    model_type: str,
    model_params: str,
    data: str,
    target_column: Optional[str] = None
) -> str:
    """使用预定义的模型进行预测

    Args:
        model_type: 模型类型
        model_params: 模型参数（JSON格式，包含训练好的模型参数）
        data: 待预测数据（JSON格式）
        target_column: 目标列名（如果有，用于计算准确率）

    Returns:
        预测结果（JSON格式）
    """
    try:
        # 这里简化处理，实际应用中应该保存和加载模型
        # 当前只返回示例
        return json.dumps({
            "success": True,
            "message": "预测功能需要先训练并保存模型，当前为简化版本"
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


# 创建LangChain工具
ml_train_tool = StructuredTool.from_function(
    func=train_model,
    name="ml_train",
    description="训练机器学习模型。支持线性回归、逻辑回归、随机森林、SVM、K-Means聚类。参数: algorithm（算法类型）, training_data（训练数据JSON）, target_column（目标列名）, params（模型参数JSON）"
)

ml_predict_tool = StructuredTool.from_function(
    func=predict_model,
    name="ml_predict",
    description="使用模型进行预测。参数: model_type（模型类型）, model_params（模型参数）, data（预测数据JSON）, target_column（目标列名，可选）"
)

# 导出所有工具
ML_TOOLS = [ml_train_tool, ml_predict_tool]
