# 公开 YOLO 权重目录与实测记录

已下载的权重放在各模型 ID 的子目录；`*.pt` 不进入 Git。来源、固定版本、SHA-256、许可证和作者公布的指标见 [catalog.json](catalog.json)。下载器每次核对 SHA-256，避免仓库更新后悄悄换掉权重。

## 选择建议

这里的“推荐”依据来源透明度、训练资料、权重可加载性、类别与后续训练便利性，不代表跨数据集的绝对精度排名。除官方 COCO 指标外，下面的 mAP 均来自作者模型卡或公开训练日志；本地另做了工地安全帽小样本框级比较。

| 方向 | 建议使用的模型 ID | 类别数 | 已公开的依据 | 选择时要注意 |
| --- | --- | ---: | --- | --- |
| 车辆/人员 | `people_vehicles` | 80 | [Ultralytics YOLO11s](https://docs.ultralytics.com/models/yolo11/)；COCO val mAP50-95 47.0 | 适合从通用目标检测开始二次训练 |
| 安全帽（骑行） | `helmet` | 2 | [模型卡](https://huggingface.co/iam-tsr/yolov8n-helmet-detection)；MIT；作者报 mAP50 0.881 | 主要展示骑行头盔，不作为当前工地项目默认模型 |
| 火焰/烟雾 | `fire_smoke` | 3 | [模型卡](https://huggingface.co/SalahALHaismawi/yolov26-fire-detection)；MIT；作者报 mAP50 0.949 | 还有 `other` 类；火灾告警用途必须用独立数据重点测漏检、误报 |
| PCB 缺陷 | `pcb` | 6 | [模型卡](https://huggingface.co/Janani-V/pcb-defect-yolov8s-deeppcb)；MIT；DeepPCB val mAP50 0.985（作者报） | 训练域偏黑白线路板图像，换相机/工艺需重新验证 |
| 道路裂缝/坑洞 | `road_damage` | 4 | [RDD2022 模型卡](https://huggingface.co/dronefreak/rdd2022-yolov8m)；AGPL-3.0；test mAP50 0.6203（作者报） | 有训练参数与同数据集对照，权重较大（52 MB） |
| 交通标志 | `traffic_sign_mit` | 36 | [模型卡和训练日志](https://huggingface.co/ankitjha07/Traffic-Sign-Detection-YOLOv8)；MIT；日志中最高 val mAP50 0.667 | 类别名称可读；区域性标志应补本地样本 |
| 病虫害：虫害 | `pest` | 102 | [IP102 模型卡](https://huggingface.co/underdogquality/yolo11s-pest-detection)；MIT；作者报 val mAP50 0.815 | 仅覆盖虫害，不等于叶片病害；类别多，需核对目标作物 |
| 病虫害：叶片病害 | `plant_disease` | 12 | [模型卡](https://huggingface.co/f4m1/plant-disease-detector-12)；作者报 held-out test mAP50 0.6277 | **未标注权重许可证**；加载还需 `albumentations>=2,<3`，暂作为本地研究候选 |
| 垃圾识别 | `waste` | 8 | [模型卡](https://huggingface.co/HrutikAdsare/waste-detection-yolov8)；MIT | 无统一 mAP；各类召回差异较大，要按自己的垃圾类别重新测 |
| PPE 劳保用品 | `ppe` | 14 | [模型卡](https://huggingface.co/jashwanthpeddisetty0712/ppe-detection-yolov8m)；AGPL-3.0；作者报 val mAP50 0.79 | 当前工地安全帽项目默认权重，只启用两类 |
| 车牌定位 | `license_plate` | 1 | [模型卡](https://huggingface.co/Murd0ck/LicensePlateDetector_YOLOv8n)；CC-BY-4.0；作者报 val mAP50 0.9807 | 仅定位，**不识别车牌字符**；训练域偏乌克兰车牌 |

另留有 `traffic_sign`：56 个数字类别的候选，作者在[模型卡](https://huggingface.co/navnani12/traffic-sign-yolov8)自报 mAP50 约 0.87，但权重未标注许可证，类别名也未映射成人可读标志。已下载并通过兼容测试，暂不作为默认推荐。

本次工地项目新增两个候选：[`hardhat_keremberke`](https://huggingface.co/keremberke/yolov8n-hard-hat-detection) 是两类小模型，来源数据集明确，但模型权重未标注许可证；[`hardhat_construction`](https://huggingface.co/baskarmother/yolov8-ppe-construction) 为 MIT 许可的 17 类工地模型。两个权重均能在当前环境加载和推理；[同一批工地图片的比较](../training/evaluations/hardhat_comparison.json)支持当前选择 `ppe`。

## 本地测试的实际范围

2026-09-29 在 Windows、PyTorch 2.14.0+cpu、Ultralytics 8.4.165 下，**14/14 个权重均能作为 `detect` 模型加载，并完成一次 640 像素、置信度 0.25 的 CPU 图片推理**。逐项类别、耗时、检出结果和所用图片记录在 [test_results.json](test_results.json)。通用模型在官方巴士样图检出 1 辆巴士和 4 人；PCB 在作者提供的原始样图产生 5 个框。安全帽、火焰样图是作者已经画过框的拼图；其余模型只用通用巴士图做运行测试。**这些框数不能当准确率，也不能证明模型在目标场景有效。**

比较精度时，需要为你选定的课题准备独立标注的测试集，固定同一图片集、类别定义、图像尺寸和阈值，再算每类 precision、recall、mAP50、mAP50-95。不同作者在不同数据集上公布的 mAP 不能直接排序。

## 下载、切换、二次训练

在项目根目录执行（PowerShell）：

```powershell
.\.venv\Scripts\python.exe model_zoo\download_models.py --samples
.\.venv\Scripts\python.exe model_zoo\test_models.py
.\.venv\Scripts\python.exe model_zoo\use_model.py ppe
```

`use_model.py` 会校验权重并复制到 `backend/models/best.pt`，同时更新模型信息页的名称。切换后重启 Flask。可选 ID 见上表或 `catalog.json`。当前工作区已激活 `ppe`；安全帽专用系统只接受同时具备佩戴与未佩戴语义的权重。若要使用 `plant_disease`，先在相同 Python 环境安装 `albumentations>=2,<3` 和 `opencv-python-headless>=4.10,<5`。

准备好自己的 YOLO 检测数据集和 `data.yaml` 后，可直接从选定权重微调：

```powershell
.\.venv\Scripts\python.exe training\train.py --model model_zoo\ppe\best.pt --data training\hardhat.yaml --epochs 50 --batch 8 --name my-hardhat --install
```

训练脚本会把最佳权重装进安全帽系统。该系统要求新权重同时包含佩戴与未佩戴安全帽语义；改做其他课题时需要同步调整后端安全帽状态映射与前端页面。`best.pt` 用于新的微调；要从中断的同一次训练继续，需保留对应训练运行的 `last.pt` 和训练配置。
