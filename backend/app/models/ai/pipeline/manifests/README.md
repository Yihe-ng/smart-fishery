# 生长识别管线 manifest（清单）使用说明

本目录下的 JSON 文件是**两阶段生长识别管线的"参数配置表"**（manifest）。
管线代码本身是固定的，**所有算法参数都从这里的 JSON 读**，改参数不用改代码。

- 生产/默认：`growth_final.json`（正式冻结清单）
- 开发/试验：`growth_candidate.example.json`（候选示例模板，**不要删**，测试依赖它）

---

## 1. 两个文件各是什么

| | `growth_final.json` | `growth_candidate.example.json` |
|---|---|---|
| 身份 | **正式冻结清单**（release_status=final） | **候选示例模板**（candidate_fixture） |
| 作用 | 线上默认使用的参数唯一真源 | 试验新模型/新参数时复制改用的模板，也是测试/ smoke 的默认清单 |
| 模型权重 | 仓库内 `releases/growth_20260808_v1/` + sha256 校验 | 借用正式权重占位（保证测试可跑） |
| 参数完整度 | 全量（分割/分类/测长质量/业务/准入策略） | 精简（只含各段核心字段） |
| 能否进生产 | 能（final） | 不能（candidate 被系统识别为试用） |

> 系统通过 `release_status` + `fixture` 两个字段区分二者，见
> `manifest.py` 的 `is_candidate_fixture()`。

---

## 2. 它是怎么"控制"管线的（数据流）

```
*.json（这张表）
  │  load_manifest() 读取 + 严格校验（缺字段/类型错/数值越界 → 直接抛错，fail fast）
  ▼
ModelManifest（内存对象）
  │  被 pipeline.py 各环节逐段读取
  ▼
分割 → 可测性分类 → 裁剪 → 视频时序 → 测长 → 业务换算 → 准入判定
```

> 权重路径、阈值、换算系数、体长分档、估重系数、准入策略——全部由清单提供，
> 代码里禁止散落硬编码。

---

## 3. 想调效果？改这里（对照表）

| 想达到的效果 | 改哪个字段 | 当前默认值 |
|---|---|---|
| 分割更"挑"（少误检，可能漏鱼） | `segmentation.conf` | 0.35 |
| 只有很确定的鱼才给测长 | `segmentation.min_confidence_for_measurement` | 0.5 |
| 可测性分类更严格 | `classifier.threshold` | 0.5 |
| 像素→厘米换算（⚠️ 0.11 是演示先验，非真实标定） | `measurement.cm_per_pixel` | 0.11 |
| 小鱼/大鱼分档线 | `business.small_threshold_cm` / `large_threshold_cm` | 15 / 25 |
| 估重公式 体重=系数×体长^指数 | `business.weight_coefficient_a` / `weight_exponent_b` | 0.0285 / 2.937 |
| 视频是否跨帧平滑（S1 时序） | `temporal.enabled_for_video` | final: true / example: false |
| 结果"严进"还是"松进" | `admission_policy.mode`（strict / geometry_rescue） | strict |

> **运行开关不在这些文件里**：管线选型 `GROWTH_PIPELINE`、清单覆盖 `GROWTH_MANIFEST_PATH`、
> 推理设备 `GROWTH_PIPELINE_DEVICE`、视频时序覆盖 `GROWTH_VIDEO_TEMPORAL_ENABLED`
> 都在 `backend/app/core/config.py`（由 `backend/.env` 覆盖）。
> 即：**"用哪个清单/在哪跑" 看 .env；"每个环节什么参数" 看这里。**

---

## 3.1 字段名速查（大白话翻译）

### 分割 / 分类（最好懂的三个）

| 字段 | 白话含义 | 调大 → | 调小 → |
|---|---|---|---|
| `segmentation.conf` | 分割置信度门槛，得分低于它的"疑似鱼"直接丢 | 更挑（漏检↑） | 更宽（误检↑） |
| `segmentation.min_confidence_for_measurement` | 分割得分达到它才允许进测长 | 更严格 | 更宽松 |
| `classifier.threshold` | 可测性分类阈值 | 更严格 | 更宽松 |

### 测长质量门槛 `measurement.quality`（最难懂的一段）

全是"几何体检"：**`min` 开头 = 低于它就拒；`max` 开头 = 超过它就拒**。

| 字段（当前值） | 白话含义 | 调大 → | 调小 → |
|---|---|---|---|
| `min_area_px` (60) | 鱼体最小像素面积，太小（太远/太偏）直接不测 | 更多小鱼不测 | 更多小鱼也测 |
| `min_solidity` (0.75) | 形状"实心度" 0~1，被咬掉一块/缺损时偏低 | 拒绝更多残缺鱼 | 容忍更多残缺 |
| `core_distance_fraction` (0.35) | 取鱼体"躯干核心"的厚度比例（提取中轴用） | — | — |
| `min_core_pixels` (20) | 躯干核心最少像素数（兜底） | — | — |
| `min_axis_stability` (10.0) | PCA 回退测长所需的方向稳定度 | 更难触发回退 | 更容易回退 |
| `straight_max_curvature_ratio` (1.18) | 允许 PCA 回退的最大弯曲度（1=笔直） | 弯一点也能回退 | 必须更直 |
| `max_curvature_ratio` (1.68) | 弯曲度上限，超过判"太弯测不了" | 更弯的鱼也测 | 更严（弯鱼拒测） |
| `max_secondary_area_ratio` (0.25) | 主鱼身外的粘连块占比上限 | 容忍更多粘连 | 更严查粘连 |
| `max_hole_area_ratio` (0.12) | 体内孔洞（反光/遮挡空洞）占比上限 | 容忍更多孔洞 | 更严查孔洞 |
| `small_hole_fill_ratio` (0.02) | 多小的孔算"小孔"、自动补上 | 补更大的孔 | 只补更小的孔 |
| `max_highlight_ratio` (0.4) | 高光（鳞片反光）像素占比上限 | 容忍更多反光 | 更严查反光 |
| `max_endpoint_count` (8) | 骨架端点（须/分叉）数量上限 | 容忍更复杂形状 | 更严 |
| `max_branch_count` (24) | 骨架分支点数量上限 | 容忍更复杂形状 | 更严 |
| `min_path_ratio` (0.45) | 主路径占骨架总长比例下限 | 更严 | 更宽 |
| `min_path_score` (0.45) | 中轴线路径可信分下限 | 更严 | 更宽 |
| `min_path_score_gap` (0.02) | 最佳 vs 次佳路径分差下限（差小=路径有歧义） | 更严 | 更宽 |
| `max_turn_rate` (0.55) | 路径转弯率上限（转太急=路径不可信） | 容忍更弯路径 | 更严 |
| `max_core_component_count` (2) | 躯干核心连通块上限（>1 可能两鱼重叠） | 容忍重叠 | 更严查重叠 |

### 业务 / 准入

| 字段（当前值） | 白话含义 | 调大 → | 调小 → |
|---|---|---|---|
| `small_threshold_cm` (15) / `large_threshold_cm` (25) | 小鱼/大鱼分档线 | 档位线更高 | 档位线更低 |
| `weight_coefficient_a` (0.0285) / `weight_exponent_b` (2.937) | 估重公式 体重=a×体长^b | 估重整体↑ | 估重整体↓ |
| `admission_policy.mode` (strict) | 准入模式：strict=体检任一不过就拒 | — | — |
| `geometry_rescue_enabled` (false) | 几何救援开关（当前只影子计算、不生效） | — | — |

---

## 3.2 调参示例（三步法）

口诀：**先想目标 → 定方向（放宽/收紧）→ 只改对应字段**。

**示例 1：远处的小鱼全被拒了**
- 目标：让更小/更远的鱼也能测出来
- 改：`measurement.quality.min_area_px` 60 → 40
- 副作用：远处模糊小鱼质量差，误测可能变多 → 可把 `classifier.threshold` 0.5 → 0.55 兜底

**示例 2：残缺、被咬掉半边的鱼也出结果**
- 目标：只测形状完整的鱼
- 改：`min_solidity` 0.75 → 0.80，`max_hole_area_ratio` 0.12 → 0.08
- 副作用：部分真实鱼被误拒（漏测↑）

**示例 3：弯曲的鱼长度忽高忽低**
- 目标：只测比较直的鱼
- 改：`max_curvature_ratio` 1.68 → 1.50，`max_turn_rate` 0.55 → 0.45
- 副作用：弯鱼被拒，有效样本变少

**示例 4：两条鱼叠在一起被当成一条**
- 目标：识别粘连/重叠
- 改：`max_secondary_area_ratio` 0.25 → 0.15，`max_core_component_count` 2 → 1

**示例 5：估重普遍偏低**
- 目标：整体抬高体重
- 改：`business.weight_coefficient_a` 0.0285 → 0.030

**通用规则**
1. 一次只调 1~2 个字段，改完跑 smoke/回归对比效果，别一把梭
2. 不知道卡在哪 → 看结果里的 `measurement_reasons`（如 `low_solidity`、`curvature_too_high`），它直接告诉你被哪条门槛拒的，对应字段一目了然
3. 只改数值，别动字段名/类型，否则启动报错（fail fast）

---

## 4. 怎么用

### 场景 A：只想微调生产参数（推荐）

直接编辑 `growth_final.json` 里的数值，重启后端生效。注意：

1. 只改数值，**不要改字段名、不要删字段、不要改类型**（否则 fail fast 启动报错）
2. `measurement.cm_per_pixel` 当前是**演示场景先验值**，要上线真实测量必须先做真实标定
3. 正式清单有权重 sha256 校验，换权重后要同步更新

### 场景 B：试验新模型 / 新参数（不影响生产）

1. 复制一份 example：`cp growth_candidate.example.json growth_candidate_xxx.json`
2. 把 `segmentation.path` / `classifier.path` / `pretrained_path` 换成你的新权重
   （候选权重放进仓库 `releases/` 目录，用相对路径，方便跨设备）
3. 按需调参数，可补上 `business` / `admission_policy` 等正式段落
4. 在 `backend/.env` 设 `GROWTH_MANIFEST_PATH=app/models/ai/pipeline/manifests/growth_candidate_xxx.json`
5. 跑 smoke/回归验证（此时 `is_candidate_fixture()=True`，系统明确是试用）
6. 满意后：把参数合并进 `growth_final.json`，把 `release_status` 保持 `final`，删除候选文件

---

## 5. 常见问题

**Q：`growth_candidate.example.json` 能删吗？**
不建议。`tests/pipeline/test_manifest.py`（含硬断言）、`tests/models/test_two_stage_pipeline_smoke.py`、
`tests/pipeline/test_model_manager.py`、`tools/smoke_growth_two_stage_pipeline.py`
都把它当默认清单引用。要删必须同步改这 4 处，且会失去"开箱即用的候选模板"。

**Q：为什么设计成"正式 + 候选"两个文件？**
防止"新模型/新参数没验证好就悄悄上线"。候选清单自带 `candidate_fixture` 标记，
系统能识别并禁止其作为正式 release；验证通过后再合并进 final。正式部署只认 final。

**Q：改坏 JSON 会怎样？**
`load_manifest()` 会 fail fast：缺字段、类型错、数值越界、release_status 非法都会直接抛错，
启动/推理立刻报错而不是静默带病运行——这是故意的设计。
