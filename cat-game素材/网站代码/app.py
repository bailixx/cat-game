import streamlit as st
import streamlit.components.v1 as components
import base64
import os

# 设置网页配置
st.set_page_config(layout="wide", page_title="小猫互动：滑动换位版")

# ==========================================
# 1. 图片处理 (保持不变，读取你的猫咪)
# ==========================================
def get_image_base64(image_path):
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_path = "mycat.png" 
img_base64 = get_image_base64(img_path)

if img_base64:
    img_src = f"data:image/png;base64,{img_base64}"
else:
    img_src = "" 
    st.error("⚠️ 没找到 mycat.png！请确保图片在同目录下。")

# ==========================================
# 2. 核心 HTML/JS 代码 (大升级)
# ==========================================

html_code = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        body { margin: 0; overflow: hidden; background-color: #f5f0e0; font-family: 'Segoe UI', sans-serif; touch-action: none; }
        #container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
        
        /* 调试窗口 */
        #debug-container {
            position: absolute; top: 10px; left: 10px; width: 160px; height: 120px; z-index: 100;
            background: #000; border-radius: 10px; overflow: hidden; border: 2px solid rgba(255,255,255,0.5);
            opacity: 0.8;
        }
        #input_video { position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0.5; transform: scaleX(-1); }
        #output_canvas { position: absolute; width: 100%; height: 100%; transform: scaleX(-1); }
        
        /* 状态文字 */
        #status-message {
            position: absolute; top: 12%; left: 50%; transform: translateX(-50%);
            font-size: 20px; font-weight: 800; color: #444; background: rgba(255,255,255,0.9);
            padding: 10px 30px; border-radius: 40px; z-index: 50; text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1); width: 70%;
            pointer-events: none; /* 让点击穿透，方便滑动 */
        }
        .hint-text { font-size: 14px; color: #888; margin-top: 5px; font-weight: normal; }
        .reward-mode { color: #E91E63 !important; border: 2px solid #E91E63; background: #fff; }

        /* 按钮 */
        #ui-controls {
            position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 10px; z-index: 50; width: 95%; justify-content: center;
        }
        .game-btn {
            padding: 15px 0; font-size: 16px; font-weight: bold; border: none; border-radius: 15px;
            color: white; cursor: pointer; box-shadow: 0 5px 0 rgba(0,0,0,0.2); flex: 1; max-width: 120px;
            transition: all 0.1s;
        }
        .game-btn:active { transform: translateY(4px); box-shadow: none; }
        .game-btn:disabled { opacity: 0.5; filter: grayscale(1); }
        
        /* 按钮颜色对应物品 */
        #btn-drink { background: linear-gradient(to bottom, #FF9800, #F57C00); } /* 橙色饮料 */
        #btn-carrot { background: linear-gradient(to bottom, #FF7043, #D84315); } /* 红色胡萝卜 */
        #btn-tissue { background: linear-gradient(to bottom, #90A4AE, #607D8B); } /* 蓝灰纸抽 */

        /* 滑动提示动画 */
        #swipe-hint {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-size: 40px; opacity: 0; pointer-events: none; z-index: 20;
            color: rgba(0,0,0,0.2); font-weight: bold;
        }

    </style>
</head>
<body>

<div id="status-message">
    准备就绪
    <div class="hint-text">👈 左右滑动屏幕可交换物品位置 👉</div>
</div>

<div id="swipe-hint">↔️</div>

<div id="debug-container">
    <video id="input_video" playsinline></video>
    <canvas id="output_canvas"></canvas>
</div>

<div id="container"></div>

<div id="ui-controls">
    <button id="btn-drink" class="game-btn">🥤 饮料</button>
    <button id="btn-carrot" class="game-btn">🥕 胡萝卜</button>
    <button id="btn-tissue" class="game-btn">🧻 纸抽</button>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.9.1/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js" crossorigin="anonymous"></script>

<script>
    // --- 注入图片 ---
    const CAT_IMAGE_SRC = "IMAGE_PLACEHOLDER"; 

    // 全局变量
    let scene, camera, renderer, catGroup;
    let itemDrink, itemCarrot, itemTissue;
    let isWaitingForReward = false;
    let isAnimating = false; // 防止狂点
    
    // 位置管理系统
    // 三个槽位的 X 坐标: 左, 中, 右
    const SLOTS = [-2.5, 0, 2.5]; 
    // 当前物品顺序数组 [左边的物品对象, 中间的, 右边的]
    let currentItems = []; 

    const statusMsg = document.getElementById('status-message');
    const buttons = document.querySelectorAll('.game-btn');
    const swipeHint = document.getElementById('swipe-hint');

    // ==========================================
    // 1. 初始化 Three.js
    // ==========================================
    function initThreeJS() {
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf5f0e0);

        camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 3.5, 7.5); // 稍微远一点，看清全景
        camera.lookAt(0, 1, 0);

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.getElementById('container').appendChild(renderer.domElement);

        // 灯光
        const ambLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambLight);
        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 10, 5);
        dirLight.castShadow = true;
        scene.add(dirLight);

        // 地板
        const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 20), new THREE.ShadowMaterial({ opacity: 0.1 }));
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        scene.add(floor);

        // 创建物体
        createCatSprite();
        createItems(); // 生成饮料、胡萝卜、纸抽

        // 动画循环
        function animate() {
            requestAnimationFrame(animate);
            // 只有当不在交换位置时，物品才自转
            if (!isAnimating) {
                if(itemDrink) itemDrink.rotation.y += 0.005;
                if(itemCarrot) itemCarrot.rotation.y += 0.005;
                if(itemTissue) itemTissue.rotation.y -= 0.005;
            }
            renderer.render(scene, camera);
        }
        animate();
        
        // 窗口自适应
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }

    // ==========================================
    // 2. 创建猫咪
    // ==========================================
    function createCatSprite() {
        catGroup = new THREE.Group();
        scene.add(catGroup);
        const loader = new THREE.TextureLoader();
        loader.load(CAT_IMAGE_SRC, (texture) => {
            const geometry = new THREE.PlaneGeometry(2.5, 3);
            const material = new THREE.MeshLambertMaterial({ map: texture, transparent: true, side: THREE.DoubleSide, alphaTest:0.5 });
            const catSprite = new THREE.Mesh(geometry, material);
            catSprite.position.y = 1.5;
            catSprite.castShadow = true;
            catGroup.add(catSprite);
        }, undefined, () => {
             const dummy = new THREE.Mesh(new THREE.BoxGeometry(1,1,1), new THREE.MeshBasicMaterial({color:0xff0000}));
             dummy.position.y = 1; catGroup.add(dummy);
        });
    }

    // ==========================================
    // 3. 创建物品 (代码生成模型)
    // ==========================================
    function createItems() {
        // --- 🥤 饮料 (Drink) ---
        itemDrink = new THREE.Group();
        // 杯身
        const cupGeo = new THREE.CylinderGeometry(0.35, 0.25, 0.9, 32);
        const cupMat = new THREE.MeshPhongMaterial({ color: 0xFF9800, transparent:true, opacity:0.9 });
        const cup = new THREE.Mesh(cupGeo, cupMat);
        cup.position.y = 0.45;
        // 杯盖
        const lid = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.05, 32), new THREE.MeshLambertMaterial({color: 0xFFFFFF}));
        lid.position.y = 0.92;
        // 吸管
        const straw = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.6, 8), new THREE.MeshLambertMaterial({color: 0x333333}));
        straw.position.set(0.1, 1.1, 0);
        straw.rotation.z = -0.2;
        
        itemDrink.add(cup, lid, straw);
        scene.add(itemDrink);

        // --- 🥕 胡萝卜 (Carrot) ---
        itemCarrot = new THREE.Group();
        const carrotBody = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.3, 1.2, 16), new THREE.MeshLambertMaterial({ color: 0xff6b35 }));
        carrotBody.position.y = 0.6; 
        itemCarrot.add(carrotBody);
        const leafGeo = new THREE.ConeGeometry(0.08, 0.4, 8);
        const leafMat = new THREE.MeshLambertMaterial({ color: 0x4CAF50 });
        for(let i=0; i<3; i++) {
            const l = new THREE.Mesh(leafGeo, leafMat);
            l.position.set(0, 1.2, 0); l.rotation.z = (Math.random()-0.5)*0.5; itemCarrot.add(l);
        }
        scene.add(itemCarrot);

        // --- 🧻 纸抽 (Tissue Box) ---
        itemTissue = new THREE.Group();
        // 盒子
        const boxGeo = new THREE.BoxGeometry(0.9, 0.5, 0.6);
        const boxMat = new THREE.MeshLambertMaterial({ color: 0x90A4AE }); // 蓝灰色盒子
        const box = new THREE.Mesh(boxGeo, boxMat);
        box.position.y = 0.25;
        // 抽出来的纸
        const paperGeo = new THREE.PlaneGeometry(0.4, 0.4);
        const paperMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, side: THREE.DoubleSide });
        const paper1 = new THREE.Mesh(paperGeo, paperMat);
        paper1.position.set(0, 0.6, 0); 
        paper1.rotation.y = 0.5;
        // 还有一半在里面
        const paper2 = new THREE.Mesh(paperGeo, paperMat);
        paper2.position.set(0, 0.5, 0);
        paper2.rotation.x = Math.PI/2;
        
        itemTissue.add(box, paper1, paper2);
        scene.add(itemTissue);

        // --- 初始化位置 ---
        // 初始顺序：饮料(左), 胡萝卜(中), 纸抽(右)
        itemDrink.position.set(SLOTS[0], 0, 2.5);
        itemCarrot.position.set(SLOTS[1], 0, 2.5);
        itemTissue.position.set(SLOTS[2], 0, 2.5);

        // 存入管理数组
        currentItems = [itemDrink, itemCarrot, itemTissue];

        // 开启阴影
        [itemDrink, itemCarrot, itemTissue].forEach(g => {
            g.traverse(c => { if(c.isMesh){c.castShadow=true; c.receiveShadow=true;} });
        });
    }

    // ==========================================
    // 4. 滑动交互逻辑 (Swipe Logic)
    // ==========================================
    
    let touchStartX = 0;
    let touchEndX = 0;

    // 监听触摸开始
    window.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, false);

    // 监听触摸结束
    window.addEventListener('touchend', (e) => {
        if(isWaitingForReward || isAnimating) return; // 忙碌时不准动

        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, false);

    // 也可以支持鼠标拖拽模拟滑动
    let isMouseDown = false;
    window.addEventListener('mousedown', e => { isMouseDown = true; touchStartX = e.clientX; });
    window.addEventListener('mouseup', e => { 
        if(!isMouseDown) return;
        isMouseDown = false; 
        if(isWaitingForReward || isAnimating) return;
        touchEndX = e.clientX; 
        handleSwipe(); 
    });

    function handleSwipe() {
        const threshold = 50; // 滑动最小距离
        const diff = touchEndX - touchStartX;

        if (Math.abs(diff) < threshold) return;

        // 向右滑 (diff > 0): 物品顺时针移动 (左->中, 中->右, 右->左)
        // 向左滑 (diff < 0): 物品逆时针移动
        if (diff > 0) {
            rotateItems(1); // Right Swipe
        } else {
            rotateItems(-1); // Left Swipe
        }
    }

    function rotateItems(direction) {
        isAnimating = true;
        
        // 显示滑动提示效果
        swipeHint.style.opacity = 1;
        gsap.to(swipeHint, {opacity: 0, duration: 1});

        // 数组操作：改变 currentItems 的顺序
        let movingItem;
        if (direction === 1) {
            // 向右滑：尾部移到头部 (右边那个飞到左边去)
            movingItem = currentItems.pop();
            currentItems.unshift(movingItem);
        } else {
            // 向左滑：头部移到尾部 (左边那个飞到右边去)
            movingItem = currentItems.shift();
            currentItems.push(movingItem);
        }

        // 动画更新所有物品的位置
        // 我们根据它们在 currentItems 数组里的新下标，飞到对应的 SLOTS 坐标
        const tl = gsap.timeline({
            onComplete: () => { isAnimating = false; }
        });

        currentItems.forEach((item, index) => {
            const targetX = SLOTS[index];
            
            // 增加一点跳跃感，让换位更可爱
            tl.to(item.position, {
                x: targetX,
                y: 0.5, // 跳起来
                duration: 0.25,
                ease: "power1.out"
            }, 0) // '0' 表示所有人同时开始
            .to(item.position, {
                y: 0, // 落地
                duration: 0.25,
                ease: "bounce.out"
            }, 0.25);
        });
    }

    // ==========================================
    // 5. 点击选择逻辑 (Updated)
    // ==========================================
    
    function handleSelection(type) {
        if(isWaitingForReward || isAnimating) return;
        buttons.forEach(b => b.disabled = true);
        
        let targetGroup, text;
        if(type==='drink') { targetGroup=itemDrink; text="饮料"; }
        if(type==='carrot') { targetGroup=itemCarrot; text="胡萝卜"; }
        if(type==='tissue') { targetGroup=itemTissue; text="纸抽"; }

        // 获取目标当前的真实 X 坐标 (因为被滑动过了)
        // 我们不需要知道它在数组的第几个，直接问 Three.js 它在哪
        const targetX = targetGroup.position.x;

        statusMsg.innerHTML = `小猫去找 ${text}...`;
        statusMsg.classList.remove('reward-mode');

        const tl = gsap.timeline();
        
        // 1. 小猫转向目标位置 (动态计算角度)
        const leanAngle = targetX * -0.1; 

        tl.to(catGroup.rotation, { z: leanAngle, x: 0.15, duration: 0.5 })
          .to(catGroup.position, { z: 1, duration: 0.5 }, "<") // 身体前倾
          
          // 2. 拍那个物品
          .to(targetGroup.position, { y: 0.8, duration: 0.2, yoyo: true, repeat: 1 }, "-=0.2") // 物品跳起
          .to(targetGroup.scale, { x:1.2, y:1.2, z:1.2, duration:0.2, yoyo:true, repeat:1 }, "<")

          // 3. 成功
          .call(() => {
              statusMsg.innerHTML = "🎉 选对啦！<br><span class='hint-text'>快伸手给摄像头喂食！</span>";
              statusMsg.classList.add('reward-mode');
              isWaitingForReward = true;
          })
          // 4. 复位
          .to(catGroup.rotation, { z: 0, x: 0, duration: 0.5 })
          .to(catGroup.position, { z: 0, duration: 0.5 }, "<");
    }

    document.getElementById('btn-drink').addEventListener('click', () => handleSelection('drink'));
    document.getElementById('btn-carrot').addEventListener('click', () => handleSelection('carrot'));
    document.getElementById('btn-tissue').addEventListener('click', () => handleSelection('tissue'));

    // ==========================================
    // 6. MediaPipe 奖励 (保持不变)
    // ==========================================
    const videoElement = document.getElementById('input_video');
    const canvasElement = document.getElementById('output_canvas');
    const canvasCtx = canvasElement.getContext('2d');

    function onHandsResults(results) {
        canvasCtx.save();
        canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            for (const landmarks of results.multiHandLandmarks) {
                drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, {color: '#00FF00', lineWidth: 2});
                drawLandmarks(canvasCtx, landmarks, {color: '#FF0000', lineWidth: 1});
            }
            if (isWaitingForReward) triggerReward();
        }
        canvasCtx.restore();
    }

    function triggerReward() {
        isWaitingForReward = false;
        statusMsg.innerHTML = "❤️ 奖励收到！好开心！ ❤️";
        
        const tl = gsap.timeline();
        tl.to(catGroup.position, { y: 2.2, duration: 0.3, yoyo: true, repeat: 1 })
          .to(catGroup.rotation, { z: 0.2, duration: 0.1, yoyo: true, repeat: 5 }, "-=0.4")
          .call(() => {
              buttons.forEach(b => b.disabled = false);
              statusMsg.classList.remove('reward-mode');
              statusMsg.innerHTML = "请滑动屏幕或选择物品";
          });
    }

    const hands = new Hands({locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`});
    hands.setOptions({ maxNumHands: 1, modelComplexity: 0, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
    hands.onResults(onHandsResults);

    const cameraMediapipe = new Camera(videoElement, {
        onFrame: async () => { await hands.send({image: videoElement}); },
        width: 320, height: 240
    });
    cameraMediapipe.start();

    initThreeJS();

</script>
</body>
</html>
"""

# ==========================================
# 3. 渲染
# ==========================================
if img_src:
    final_html = html_code.replace("IMAGE_PLACEHOLDER", img_src)
else:
    final_html = html_code

components.html(final_html, height=800, scrolling=False)