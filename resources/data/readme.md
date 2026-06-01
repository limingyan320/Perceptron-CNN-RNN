# 验证码 OCR 数据集说明

本目录包含用于训练四位验证码 OCR 模型的数据。验证码图片来自同一种验证码生成器，适合做特定场景下的轻量 OCR 模型训练、评估和部署验证。

## 目录结构

```text
data/
├── raw/                 原始验证码图片及采集元数据
├── labels/              标签 CSV 文件
├── processed/           预处理或临时派生产物，当前不作为标准交付内容
└── readme.md            本说明文件
```

## 数据概况

- 图片数量：1381 张有效验证码图片
- 图片尺寸：固定为 `82x31`
- 图片格式：主要为 JPG，早期少量样本为 PNG
- 验证码长度：固定 4 位
- 字符集：`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`
- 类别数：36 类
- 推荐标签文件：`data/labels/labels_reviewed_round5.csv`
- 推荐标签文件有效样本数：1330 条

说明：`data/raw/` 中可能包含采集元数据 CSV，不应当按图片读取。

## 标签文件说明

标签文件位于 `data/labels/`，CSV 字段如下：

| 字段 | 含义 |
| --- | --- |
| `path` | 图片相对路径，例如 `data/raw/captcha_20260525_004938_1.png` |
| `label` | 人工审核后的 4 位验证码文本，已统一为大写 |
| `raw_response` | 预标注阶段模型的原始输出或参考值 |
| `valid` | 是否可用于训练，`1` 表示有效，`0` 表示无效或不确定 |

推荐使用最新审核版本：

```text
data/labels/labels_reviewed_round5.csv
```

其他标签文件含义：

| 文件 | 用途 |
| --- | --- |
| `prelabels.csv` | 多模态模型预标注结果，未充分人工审核 |
| `labels_upper.csv` | 将预标注结果统一转成大写后的中间版本 |
| `labels_reviewed.csv` | 第一轮人工审核后的标签 |
| `labels_reviewed_round2.csv` ~ `labels_reviewed_round5.csv` | 多轮 bad case 审核后的标签版本 |

## 使用建议

训练时建议只使用满足以下条件的样本：

1. `valid == 1`
2. `label` 长度为 4
3. `label` 中字符属于 `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`
4. `path` 指向的图片文件存在且可正常读取

Python 读取示例：

```python
import csv
from pathlib import Path

label_file = Path("data/labels/labels_reviewed_round5.csv")

rows = []
with label_file.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        label = row["label"].strip().upper()
        image_path = Path(row["path"])
        if row.get("valid") != "1":
            continue
        if len(label) != 4:
            continue
        if not image_path.exists():
            continue
        rows.append({"path": str(image_path), "label": label})

print(len(rows))
```

## 标注质量

本数据集的标签流程为：

1. 自动采集验证码原图。
2. 使用多模态模型进行预标注。
3. 将标签统一转为大写。
4. 使用训练模型预测训练集、验证集和测试集。
5. 对预测结果与标签不一致的 bad case 进行多轮人工审核。

因此，`labels_reviewed_round5.csv` 是当前最推荐的标签版本。仍需注意，`0/O`、`1/I`、`5/S` 等相似字符存在天然视觉歧义，个别样本可能仍有争议。

## 数据导出建议

如果将数据交付给其他人，建议至少包含：

```text
data/readme.md
data/raw/
data/labels/labels_reviewed_round5.csv
```

可选包含：

```text
data/labels/prelabels.csv
data/labels/labels_upper.csv
data/labels/labels_reviewed*.csv
```

如果只希望交付最终可训练数据，保留 `labels_reviewed_round5.csv` 即可。

## 适用范围

该数据集适合训练特定验证码样式的固定四位 OCR 模型，不适合作为通用 OCR 数据集。模型或数据用于第三方系统前，应确认具备相应授权。
