#3D AI 虚拟猫咪互动系统

[cite_start]一个基于浏览器运行的 3D 虚拟宠物互动引擎。本项目打破了常规的网页交互限制，将Three.js的3D渲染与MediaPipe的计算机视觉（CV）手势追踪技术完美融合，打造了一个可以通过滑动屏幕、点击和真实手势喂食的沉浸式 AI 互动体验 。

#核心特性

1.计算机视觉手势互动：接入 MediaPipe Hands 视觉模型。当你在摄像头前伸出手时，系统会实时捕捉手部关键点（Landmarks），触发猫咪的“奖励”互动反馈 。

2.纯代码级 3D 渲染：借助 Three.js，无需外部加载任何 `.gltf` 模型，全代码动态生成场景、灯光、阴影以及 3D 互动道具（饮料、胡萝卜、纸抽） 。

3.物理级丝滑动画：集成 GSAP 动画引擎。支持鼠标拖拽或触屏滑动操作，实现 3D 物品位置的无缝轮转与弹跳缓动效果 。

4.自定义宠物皮肤：支持一键替换猫咪贴图（2.5D Sprite 渲染），轻松将你自己的猫咪植入 3D 虚拟世界 。

#技术架构

1.宿主框架：Python / Streamlit [cite: 2] [cite_start](用于快速搭建 Web 服务与 Base64 图像处理 )

2.3D 引擎：Three.js (r128) 

3.动画系统：GSAP (3.9.1) 

4.AI 视觉追踪：MediaPipe Hands (JavaScript API) 

#快速开始

#1.克隆项目

bash

git clone [https://github.com/bailixx/cat-game.git](https://github.com/bailixx/cat-game.git)

cd cat-game

页面图片

<img width="1715" height="840" alt="小猫游戏网页前端页面" src="https://github.com/user-attachments/assets/628b47da-db45-4310-a051-1506196f28f8" />

