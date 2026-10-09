# 骑行赛段透明仪表盘

将骑行赛段数据渲染成 **4K60透明MOV**，在剪辑软件中直接叠加到第一人称骑行视频上。项目包括可单独使用的Python脚本和Codex Skill。

[English](README.md) · [数据格式](references/data.md)

![虚构路线演示](docs/demo-preview.jpg)

上图路线、功率和心率均为程序生成的虚构数据。灰底仅用于预览，导出视频保留透明通道。

## 功能

- 功率、心率、踏频、速度、距离、爬升、用时及功体比。
- 自定义分段计时、平均功率和心率，当前段展开、完成段记录。
- GPS动态地图、完成星标、坡度与高程图、底部功率/心率历史。
- 分块渲染、断点续渲染、无损拼接和透明通道检查。

默认输出3840×2160、60fps、qtrle/ARGB透明MOV，无音轨。画面布局按1080p绘制并放大至4K，动效逐帧60fps生成；不宣称原生4K字体绘制。

界面灵感来自骑行游戏，本项目与Zwift及Strava无隶属或合作关系。公开版使用OFL开源Tektur字体，未包含Zwift专有字体、截图或录像。也可通过配置中的font_path指定自己有权使用的本地字体。

## 安装与运行

需要Python3.10+、FFmpeg及ffprobe。macOS可运行 `brew install ffmpeg`，Ubuntu可运行 `sudo apt-get install ffmpeg`。

```sh
git clone https://github.com/Just-blue/data-dashboard-skills.git
cd data-dashboard-skills/skills/zwift-segment-hud
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/make_demo.py
python scripts/hud.py --config examples/demo/config.json \
  --output-dir outputs/preview --at 55 --width 1920
python scripts/hud.py --config examples/demo/config.json \
  --output-dir outputs/sample --mode video --begin 39 --duration 3
```

演示无需登录任何平台。短片输出在 `outputs/sample/hud-alpha.mov`，放到原视频上方轨道并按Alpha合成，无需抠黑底。完整导出时去掉begin/duration参数并指定新的输出目录。

## 作为全局Skill安装

在集合仓库根目录运行：

```sh
python3 scripts/install_skill.py zwift-segment-hud
```

只安装当前仪表盘，已有同名目录时会停止，避免覆盖个人定制。依赖安装和更新方式见[集合说明](../../README.zh-CN.md)。然后在新对话中使用：

> 使用 $zwift-segment-hud，根据这个活动中的赛段生成透明4K60仪表盘：赛段成绩链接。

## 真实活动需要什么

需要已确认边界的赛段CSV，以及名字、活动当日体重、FTP和数据来源配置。CSV格式见[数据说明](references/data.md)。数据时间轴从0开始，完整1Hz采样，包含终点，保留停止时间。

Strava链接不是脚本直接输入：登录、下载、FIT转换和跨平台活动匹配尚未内置。Skill可以由代理结合已授权工具组织这些步骤，不能保证只有一个链接就无人干预完成。活动中的某次赛段成绩链接能够确定尝试；普通赛段链接通常还需确定是哪次活动。

当前不支持自动填补传感器缺失、不规则采样或非整数秒赛段时长。不能把缺失功率/心率当0。PR/KOM对比尚未实现。分段为自定义展示段，不是Strava官方子赛段。原视频对时需要单独校准。

中断后用相同命令续渲染；输入或代码变化会拒绝复用旧块。无损透明视频体积较大，需同时容纳中间块和最终文件。每次导出附verification.json，检查规格、透明和拼接点，并仍需目视抽查。

代码与文档使用[MIT许可证](LICENSE)；Tektur字体单独适用[OFL1.1](assets/OFL.txt)。
