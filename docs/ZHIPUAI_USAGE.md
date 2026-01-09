# 使用智谱AI运行数据开发Agent

本项目已集成智谱AI（BigModel）支持，可以使用GLM-4系列模型。

## 快速开始

### 方法1：使用启动脚本（推荐）

**Linux/macOS:**
```bash
./run_zhipu.sh
```

**Windows:**
```cmd
run_zhipu.bat
```

### 方法2：手动启动

```bash
python -m data_agent.main \
    --provider zhipu \
    --api-key a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8 \
    --model glm-4 \
    --base-url https://open.bigmodel.cn/api/paas/v4
```

## 参数说明

- `--provider`: LLM提供商，设置为 `zhipu`
- `--api-key`: 智谱AI API密钥
- `--model`: 模型名称
  - `glm-4`: GLM-4标准版
  - `glm-4-plus`: GLM-4增强版
  - `glm-4-0520`: GLM-4特定版本
- `--base-url`: API基础URL（默认: https://open.bigmodel.cn/api/paas/v4）
- `--db`: 数据库连接字符串（可选）

## 示例

### 基础使用
```bash
python -m data_agent.main \
    --provider zhipu \
    --api-key your-api-key \
    --model glm-4
```

### 使用数据库
```bash
python -m data_agent.main \
    --provider zhipu \
    --api-key your-api-key \
    --model glm-4 \
    --db "mysql+pymysql://user:password@localhost:3306/database"
```

### 使用增强模型
```bash
python -m data_agent.main \
    --provider zhipu \
    --api-key your-api-key \
    --model glm-4-plus
```

## 环境变量配置

也可以通过环境变量设置API密钥：

```bash
export ZHIPUAI_API_KEY="your-api-key"
python -m data_agent.main --provider zhipu
```

## 切换回Anthropic

如果要使用Anthropic Claude：

```bash
python -m data_agent.main \
    --provider anthropic \
    --api-key your-anthropic-key \
    --model claude-sonnet-4-5-20250929
```

## 注意事项

1. 确保已安装 `zhipuai` 包：
   ```bash
   pip install zhipuai
   ```

2. API密钥格式：智谱AI的密钥格式为 `id.secret`
   - 示例：`a2d9aad92f254c17b3c71495177cc94b.vXbdUFVOvhGZnqf8`

3. 模型选择：
   - `glm-4`: 标准版，适合一般任务
   - `glm-4-plus`: 增强版，性能更强
   - `glm-4-0520`: 特定版本

4. API限制：注意智谱AI的API调用频率限制

## 故障排查

### 导入错误
如果遇到 `No module named 'zhipuai'` 错误：
```bash
pip install zhipuai
```

### API调用失败
1. 检查API密钥是否正确
2. 检查网络连接
3. 确认API额度是否充足
4. 检查base_url是否正确

### 模型不支持
如果提示模型不支持，请检查：
1. 模型名称拼写是否正确
2. 是否有权限使用该模型
3. 尝试使用 `glm-4` 作为默认模型

## 更多信息

- 智谱AI官网: https://open.bigmodel.cn/
- 智谱AI文档: https://open.bigmodel.cn/dev/api
