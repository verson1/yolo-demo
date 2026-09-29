# 基于 YOLO 的安全帽佩戴检测系统

面向工地图片和短视频，识别“已佩戴安全帽”和“未佩戴安全帽”的目标，保存检测结果并统计未佩戴情况。系统由 Vue 3、Flask、Ultralytics YOLO 和 MySQL 8 组成。当前使用已训练的工地 PPE YOLOv8m 权重，推理时只启用 `Hardhat` 与 `NO-Hardhat` 两类；替换成其他同时具备这两类语义的 YOLO 检测权重后也可运行。

## 已实现

- 图片检测：上传、置信度设置、标注图、两类目标框和未佩戴提醒。
- 视频检测：逐帧标注并生成 MP4，统计两类检测框及出现未佩戴目标的帧数。
- 检测记录：原始文件、结果文件、佩戴统计、详情和删除。
- 数据看板：当前模型的任务数量、两类目标分布、未佩戴任务趋势。
- 模型与训练：校验并切换公开权重、下载公开数据、微调、预览和本地比较。

“未检出目标”显示为**未知**。视频检测框跨帧重复计数，不能当作独立工人人数；本系统不做人脸识别或人员跟踪。

## 安装和运行

需要 Python 3.11 或 3.12、Node.js 20.19+ 或 22.12+、MySQL 8。当前工作区已有权重；重新克隆项目时 `.pt` 权重不会随 Git 下载。

1. 使用 MySQL Workbench 执行 [建库脚本](backend/schema.sql)。如果数据库是旧版通用模板创建的，先备份，再运行 `python backend/migrate.py`；旧记录会标为 `legacy`，当前看板只显示当前模型记录。
2. 在项目根目录安装并启动后端：

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   $env:MYSQL_USER = 'root'
   $env:MYSQL_PASSWORD = '你的 MySQL 密码'
   .\.venv\Scripts\python.exe model_zoo\download_models.py ppe
   .\.venv\Scripts\python.exe model_zoo\use_model.py ppe
   .\.venv\Scripts\python.exe backend\app.py
   ```

3. 在另一个终端启动前端：

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

前端通常为 `http://127.0.0.1:5173`，后端为 `http://127.0.0.1:5000`。修改模型文件或后端配置后重启 Flask。模型路径、系统标题、数据库连接、上传大小和置信度默认值位于 [配置文件](backend/config.py)，也可由同名环境变量覆盖。

## 训练自己的安全帽模型

公开的 [Hard Hats 数据集](https://huggingface.co/datasets/keremberke/hard-hat-detection)有 `Hardhat`、`NO-Hardhat` 两类，采用 CC BY 4.0 许可，并提供训练、验证、测试划分。使用[数据准备脚本](training/prepare_hardhat_data.py)把它转为 Ultralytics YOLO 格式，类别顺序写在 [hardhat.yaml](training/hardhat.yaml)。

```powershell
# 快速验证训练流程的小样本；当前工作区已准备 128/32/48 张
.\.venv\Scripts\python.exe training\prepare_hardhat_data.py --train 128 --val 32 --test 48

# 正式复训时可下载公开数据的全部划分，约 1.12 GB
.\.venv\Scripts\python.exe training\prepare_hardhat_data.py --train 13782 --val 3962 --test 2001

# GPU 示例；没有 GPU 可改为 --device cpu，并调小 batch
.\.venv\Scripts\python.exe training\train.py --data training\hardhat.yaml --model model_zoo\ppe\best.pt --device 0 --epochs 50 --batch 8 --name hardhat-v1 --install
```

`--install` 会把训练出的最佳权重接入系统。小样本适合检查训练流程，不能代替完整训练或精度评价。不要把测试集用于训练或调参。

已准备 128 张训练图和 32 张验证图，并用其中 13 张训练图、32 张验证图完成 1 轮 CPU 流程检查。生成的两类权重位于 `training/runs/hardhat-smoke/weights/best.pt`（不进入 Git）。这只证明数据读取、训练、验证、生成权重和重新加载可以运行；默认系统仍使用上面的公开 PPE 权重。

## 选模与测试依据

此前的两类 `helmet` 权重主要展示骑行头盔；本项目比较了四个候选在上述公开工地数据集前 48 张测试图上的检测框。在置信度 0.25、IoU 0.5 下，当前 PPE 权重的安全帽类 Precision/Recall 为 **0.912/0.963**，未佩戴类为 **0.947/0.857**。具体 TP、FP、FN 及各模型结果见[比较记录](training/evaluations/hardhat_comparison.json)。这是小样本工程对比，无法排除模型训练数据与该测试集重叠，也不是完整 mAP 评估。当前权重的[模型卡](https://huggingface.co/jashwanthpeddisetty0712/ppe-detection-yolov8m)提供训练信息和作者报告的验证指标。

已验证图片和四帧视频从接口上传、模型推理、MySQL 保存、结果文件读取到记录删除的完整流程。可用[接口检查脚本](backend/smoke_test.py)在有 MySQL 和测试图片的环境中复查：

```powershell
.\.venv\Scripts\python.exe backend\smoke_test.py training\dataset\hardhat\images\test\000001.jpg
```

其余公开权重、来源和下载方法保留在[模型目录](model_zoo/README.md)。使用第三方数据和权重时应遵守各自模型卡与数据集的许可要求。
