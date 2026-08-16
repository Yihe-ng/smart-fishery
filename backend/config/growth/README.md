# 生长识别配置目录（模型清单 + 养殖标准）

本目录是生长识别相关**配置的唯一存放位置**，包含两类彼此独立的配置：

| 文件 | 类别 | 负责什么 |
|---|---|---|
| `pipeline.final.json` | 模型清单（manifest） | 正式冻结清单：分割/分类模型与权重、裁剪方式、视频时序策略、测长算法与几何质量门槛、像素→厘米换算、可测性准入策略 |
| `pipeline.candidate.example.json` | 模型清单（manifest） | 候选示例模板（`candidate_fixture`），试验新模型/新参数时复制改用，也是测试/smoke 的默认清单。**不要删**，多处测试依赖 |
| `grouper_growth_standard.json` | 养殖标准 | 月度生长评价业务规则：第 3–15 个月预期累计增长量、每月偏小/偏大比例、群体最小样本与去极端规则、体长估重公式、视频临时旧分档规则 |

## 1. 职责边界（重要）

- **模型清单只管"怎么测"**：模型在哪、阈值多少、几何质量怎么卡、像素怎么换成厘米。
- **养殖标准只管"测出来怎么评"**：这条鱼相对本月参考全长是偏小/正常/偏大，鱼群整体如何，给出什么管理方向。
- **`backend/app/core/config.py` / `backend/.env` 只管"用哪个文件、在哪跑"**：`GROWTH_PIPELINE`（管线选型）、`GROWTH_MANIFEST_PATH`（清单覆盖）、`GROWTH_STANDARD_PATH`（养殖标准覆盖）、`GROWTH_PIPELINE_DEVICE`（推理设备）、`GROWTH_VIDEO_TEMPORAL_ENABLED`（视频时序覆盖）。

体长分档（偏小/偏大）和估重公式**曾经**放在模型清单的 `business` 段，现已全部迁到 `grouper_growth_standard.json`。模型清单不再有 `business` 段，代码也不再解析它。

## 2. 养殖标准的资料依据

月度预期增长量来自以下公开资料的综合，不是任何单一论文的结论：

- 彭树锋、王云新、叶富良、张海发，《工厂化养殖斜带石斑鱼生长研究》，中国水产，2008(7):56–58。初始平均全长约 12.9 cm，约 240 天后达 25.5 cm，线性关系 `L = 0.0504t + 13.231`，对应月均增长约 1.51 cm。
- [棕点石斑鱼不同月龄生长研究](http://scxuebao.ijournals.cn/html/scxuebao/2017/7/20161010596.htm)：提供 3、8、13 生物学月龄全长数据。
- [云龙石斑鱼生长研究](https://xuebao.dlou.edu.cn/article/2019/2095-1388/201905011.html)：提供 4、9、15 生物学月龄全长数据。
- [赤点石斑鱼 365 天养殖研究](https://pdf.hanspub.org/OJFR20160300000_92446660.pdf)：初始全长约 13.8 cm，365 天后约 20.7–21.9 cm，说明品种与养殖条件差异明显。
- [杂交石斑鱼投喂频次研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC11816143/)：高脂饲料试验中每日 2 次优于 1 次，继续增加频次未持续改善生长——所以不能由"偏小"直接推出"继续加料"。

### 综合增长量口径

采用约 **1.5 cm/月** 作为初始工程参考，并把每个月的**累计**预期增长量显式写入 JSON（不是代码里的公式），后续可逐月独立调整：

| 投苗后月份 | expected_gain_cm |
| ---: | ---: |
| 3 | 4.5 |
| 4 | 6.0 |
| 5 | 7.5 |
| 6 | 9.0 |
| 7 | 10.5 |
| 8 | 12.0 |
| 9 | 13.5 |
| 10 | 15.0 |
| 11 | 16.5 |
| 12 | 18.0 |
| 13 | 19.5 |
| 14 | 21.0 |
| 15 | 22.5 |

**第 13–15 个月属于综合趋势外推区间**，可用资料只覆盖到约 13–15 生物学月龄且品种不一致，这三个月的数值置信度低于前面月份。该说明只写在本文件，不进入前端。

### ±15% 是工程容差，不是论文结论

`small_ratio = 0.85` / `large_ratio = 1.15` 意味着以综合参考全长的 ±15% 作为偏小/偏大分档线。**目前没有检索到规定石斑鱼应按 ±15% 分档的论文或行业标准**，它是一个保守的、可修改的工程容差。前端因此统一称"综合参考全长"，禁止表述为"论文规定体长""行业标准体长"。

## 3. 养殖标准字段含义

```json
{
  "schema_version": 1,
  "cohort_rule": { "min_measurable_count": 3, "drop_shortest_count": 1 },
  "weight_estimation": { "coefficient_a": 0.0285, "exponent_b": 2.937 },
  "monthly_rules": { "3": { "expected_gain_cm": 4.5, "small_ratio": 0.85, "large_ratio": 1.15 } },
  "legacy_video_rule": { "temporary": true, "small_threshold_cm": 15.0, "large_threshold_cm": 25.0 }
}
```

| 字段 | 含义 |
|---|---|
| `schema_version` | 配置结构版本，当前仅支持 `1` |
| `cohort_rule.min_measurable_count` | 群体评价所需的最少可测鱼数量，低于它群体状态为"样本不足"（不低于 3） |
| `cohort_rule.drop_shortest_count` | 群体评价前去掉的最短记录条数（当前为 1；最短值并列时也只去掉一条），必须小于 `min_measurable_count` |
| `weight_estimation.coefficient_a` / `exponent_b` | 估重公式 `体重(g) = a × 全长(cm) ^ b` 的系数与指数，均须为正数 |
| `monthly_rules.<月>.expected_gain_cm` | 该月相对投苗时平均全长的**累计**预期增长量（cm），须为正且不随月份下降 |
| `monthly_rules.<月>.small_ratio` | 偏小下限比例，须满足 `0 < small_ratio < 1` |
| `monthly_rules.<月>.large_ratio` | 偏大上限比例，须满足 `large_ratio > 1` |
| `legacy_video_rule` | 视频路径的临时固定分档，见下节 |

计算口径：

```text
当月综合参考全长 = 投苗时平均全长 + monthly_rules[月].expected_gain_cm
偏小下限 = 综合参考全长 × small_ratio
偏大上限 = 综合参考全长 × large_ratio
```

个体状态边界（一律用未四舍五入的原始值判断，四舍五入只发生在展示层）：

- `< 偏小下限` → 偏小
- `>= 偏小下限` 且 `<= 偏大上限` → 正常
- `> 偏大上限` → 偏大
- 可测但没有养殖月数/投苗体长 → **未评估**（不是"不可测"，也不回退任何固定阈值）
- 无法可靠测长 → 不可测（不参与任何平均值）

## 4. `legacy_video_rule` 是临时兼容，不是业务标准

配置拆分之前，图片和视频共用固定的 15 / 25 cm 分档。为了让本期拆分**不改变视频行为**，把这两个固定阈值原样迁到 `legacy_video_rule`：

- **仅视频路径读取**（`backend/app/api/v1/endpoints/growth.py` 的视频分帧分档）。
- **图片路径禁止读取**，也不作为图片评价失败时的回退规则——图片评价失败时可测鱼一律显示"未评估"。
- `temporary: true` 是强制标记，缺失或为 false 时加载直接失败。
- 后续视频月度评价改造必须补齐养殖月份与投苗体长，并复用同一套评价服务；改造完成后删除本段。

这是一项明确的技术债，不应被解释为长期业务标准。

## 5. 读取、校验与生效

- 后端在需要时读取并**严格校验**这两类配置，解析结果在进程内缓存，接口请求不重复读盘。
- **修改任何 JSON 后必须重启后端才能生效**（没有热加载）。
- 模型清单错误 → 图片识别不可用（fail fast，缺字段/类型错/数值越界直接抛错）。
- 养殖标准错误 → 模型测量仍可用，但生长评价降级为"未评估"，不产生群体分档与投喂方向；具体文件、字段和校验错误只记录到后端终端日志，不返回给前端。
- 养殖标准校验项：第 3–15 个月完整无缺无重复、增长量为正且不下降、`0 < small_ratio < 1`、`large_ratio > 1`、`min_measurable_count >= 3`、`drop_shortest_count < min_measurable_count`、估重系数与指数为正、`legacy_video_rule.temporary == true`。

## 6. 模型清单：两个文件的区别

| | `pipeline.final.json` | `pipeline.candidate.example.json` |
|---|---|---|
| 身份 | 正式冻结清单（`release_status=final`） | 候选示例模板（`fixture.type=candidate_fixture`） |
| 作用 | 线上默认使用的模型参数唯一真源 | 试验新模型/新参数时复制改用的模板，也是测试/smoke 的默认清单 |
| 模型权重 | 仓库内 `app/models/ai/releases/growth_20260808_v1/` + sha256 校验 | 借用正式权重占位（保证测试可跑） |
| 参数完整度 | 全量（分割/分类/测长质量/换算/准入策略） | 精简（只含各段核心字段） |
| 能否进生产 | 能 | 不能（`is_candidate_fixture()` 会识别为试用） |

清单如何驱动管线：

```text
*.json
  │  load_manifest() 读取 + 严格校验（缺字段/类型错/数值越界 → 直接抛错，fail fast）
  ▼
ModelManifest（内存对象）
  │  被 pipeline.py 各环节逐段读取
  ▼
分割 → 可测性分类 → 裁剪 → 视频时序 → 测长 → 厘米换算 → 准入判定
```

## 7. 模型清单常用可调字段

| 想达到的效果 | 改哪个字段 | 当前值 |
|---|---|---|
| 分割更"挑"（少误检，可能漏鱼） | `segmentation.conf` | 0.35 |
| 只有很确定的鱼才给测长 | `segmentation.min_confidence_for_measurement` | 0.5 |
| 可测性分类更严格 | `classifier.threshold` | 0.5 |
| 像素→厘米换算（⚠️ 演示场景先验，非真实标定） | `measurement.scale.cm_per_pixel` | 0.08 |
| 视频是否跨帧平滑（S1 时序） | `temporal.enabled_for_video` | final: true / example: false |
| 结果"严进"还是"松进" | `admission_policy.mode`（strict / geometry_rescue） | final: geometry_rescue |

### 测长质量门槛 `measurement.quality`

全是"几何体检"：**`min` 开头 = 低于它就拒；`max` 开头 = 超过它就拒**。

| 字段（final 当前值） | 含义 | 调大 → | 调小 → |
|---|---|---|---|
| `min_area_px` (60) | 鱼体最小像素面积，太小（太远/太偏）直接不测 | 更多小鱼不测 | 更多小鱼也测 |
| `min_solidity` (0.75) | 形状"实心度" 0~1，缺损时偏低 | 拒绝更多残缺鱼 | 容忍更多残缺 |
| `core_distance_fraction` (0.35) | 取躯干核心的厚度比例（提取中轴用） | — | — |
| `min_core_pixels` (20) | 躯干核心最少像素数（兜底） | — | — |
| `min_axis_stability` (10.0) | PCA 回退测长所需的方向稳定度 | 更难触发回退 | 更容易回退 |
| `straight_max_curvature_ratio` (1.18) | 允许 PCA 回退的最大弯曲度（1=笔直） | 弯一点也能回退 | 必须更直 |
| `max_curvature_ratio` (1.68) | 弯曲度上限，超过判"太弯测不了" | 更弯的鱼也测 | 弯鱼拒测 |
| `max_secondary_area_ratio` (0.25) | 主鱼身外粘连块占比上限 | 容忍更多粘连 | 更严查粘连 |
| `max_hole_area_ratio` (0.12) | 体内孔洞（反光/遮挡）占比上限 | 容忍更多孔洞 | 更严查孔洞 |
| `small_hole_fill_ratio` (0.02) | 多小的孔算"小孔"、自动补上 | 补更大的孔 | 只补更小的孔 |
| `max_highlight_ratio` (0.4) | 高光（鳞片反光）像素占比上限 | 容忍更多反光 | 更严查反光 |
| `max_endpoint_count` (8) | 骨架端点（须/分叉）数量上限 | 容忍更复杂形状 | 更严 |
| `max_branch_count` (24) | 骨架分支点数量上限 | 容忍更复杂形状 | 更严 |
| `min_path_ratio` (0.45) | 主路径占骨架总长比例下限 | 更严 | 更宽 |
| `min_path_score` (0.45) | 中轴线路径可信分下限 | 更严 | 更宽 |
| `min_path_score_gap` (0.02) | 最佳 vs 次佳路径分差下限（差小=路径有歧义） | 更严 | 更宽 |
| `max_turn_rate` (0.55) | 路径转弯率上限（转太急=路径不可信） | 容忍更弯路径 | 更严 |
| `max_core_component_count` (2) | 躯干核心连通块上限（>1 可能两鱼重叠） | 容忍重叠 | 更严查重叠 |

调参口诀：**先想目标 → 定方向（放宽/收紧）→ 只改对应字段**。一次只调 1~2 个字段，改完跑 smoke/回归对比。不知道卡在哪就看结果里的 `measurement_reasons`（如 `low_solidity`、`curvature_too_high`），它直接告诉你被哪条门槛拒的。

## 8. 怎么用

### 场景 A：微调生产参数（推荐）

直接编辑对应 JSON 的数值，重启后端生效。注意：

1. 只改数值，**不要改字段名、不要删字段、不要改类型**（否则 fail fast 启动报错）。
2. `measurement.scale.cm_per_pixel` 当前是演示场景先验值，要上线真实测量必须先做真实标定。
3. 正式清单有权重 sha256 校验，换权重后要同步更新。
4. 改月度增长量/分档比例改 `grouper_growth_standard.json`，不要改模型清单。

### 场景 B：试验新模型 / 新参数（不影响生产）

1. 复制一份 example：`cp pipeline.candidate.example.json pipeline.candidate.xxx.json`
2. 把 `segmentation.path` / `classifier.path` / `pretrained_path` 换成新权重（候选权重放进仓库 `app/models/ai/releases/`，用相对路径，方便跨设备）。
3. 按需调参数，可补上 `admission_policy` 等正式段落。
4. 在 `backend/.env` 设 `GROWTH_MANIFEST_PATH=config/growth/pipeline.candidate.xxx.json`。
5. 跑 smoke/回归验证（此时 `is_candidate_fixture()=True`，系统明确是试用）。
6. 满意后：把参数合并进 `pipeline.final.json`（保持 `release_status=final`），删除候选文件。

## 9. 常见问题

**Q：`pipeline.candidate.example.json` 能删吗？**
不建议。`tests/pipeline/test_manifest.py`（含硬断言）、`tests/models/test_two_stage_pipeline_smoke.py`、
`tests/pipeline/test_model_manager.py`、`tools/smoke_growth_two_stage_pipeline.py` 都把它当默认清单引用。

**Q：为什么设计成"正式 + 候选"两个清单？**
防止"新模型/新参数没验证好就悄悄上线"。候选清单自带 `candidate_fixture` 标记，系统能识别并禁止其作为正式 release；验证通过后再合并进 final。

**Q：改坏 JSON 会怎样？**
模型清单 `load_manifest()` fail fast，启动/推理立刻报错——这是故意的设计。养殖标准 `load_growth_standard()` 同样严格校验，但失败只降级生长评价（可测鱼显示"未评估"），不影响体长测量。
