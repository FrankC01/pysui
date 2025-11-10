# 新概念英语学习APP

一个基于React Native (Expo) 开发的新概念英语音频学习应用，支持Android和iOS平台。

## 功能特性

### 1. 首页模块
- 显示新概念英语第一册至第四册的课文列表
- 顶部下拉选择器可快速切换不同册数
- 点击课文进入播放界面

### 2. 音频播放界面
- **中英文对照**: 可切换显示/隐藏中文翻译
- **单句循环**: 支持单句重复播放
- **播放速度控制**: 支持0.5x、0.75x、1.0x、1.25x、1.5x、2.0x多种速度
- **播放次数显示**: 记录总播放次数和每句的播放次数
- **句子导航**: 可点击任意句子进行播放
- **播放控制**: 上一句、下一句、播放/暂停

### 3. 课程模块
- 以图文列表形式展示四册书
- 显示每册的副标题、描述和课程数量
- 点击可快速跳转到对应册数的课文列表

### 4. 我的模块
- 用户登录/注册界面
- 登录后显示用户信息
- 学习统计（学习天数、已学课程）
- 功能菜单（收藏、学习记录、设置、帮助）
- 退出登录功能

## 技术栈

- **框架**: React Native (Expo)
- **导航**: React Navigation (Bottom Tabs + Stack Navigator)
- **UI组件**: React Native原生组件
- **音频**: Expo AV
- **图标**: @expo/vector-icons (Ionicons)
- **选择器**: @react-native-picker/picker

## 项目结构

```
AudioApp/
├── App.js                          # 应用入口
├── src/
│   ├── navigation/                 # 导航配置
│   │   ├── AppNavigator.js        # 主导航（Stack）
│   │   └── BottomTabNavigator.js  # 底部标签导航
│   ├── screens/                    # 页面组件
│   │   ├── HomeScreen.js          # 首页
│   │   ├── PlayerScreen.js        # 音频播放页
│   │   ├── CoursesScreen.js       # 课程列表页
│   │   └── ProfileScreen.js       # 个人中心页
│   ├── components/                 # 可复用组件（预留）
│   ├── data/                       # 数据文件
│   │   └── lessonsData.js         # 课文数据
│   └── utils/                      # 工具函数（预留）
├── assets/                         # 资源文件
└── package.json                    # 项目依赖
```

## 安装与运行

### 前置要求
- Node.js >= 14
- npm 或 yarn
- Expo CLI (可选，已集成到项目中)

### 安装依赖
```bash
cd AudioApp
npm install
```

### 运行项目

#### 开发模式
```bash
# 启动开发服务器
npm start

# 或指定平台
npm run android   # Android平台
npm run ios       # iOS平台（需要macOS）
npm run web       # Web平台
```

#### 在真机上测试
1. 在手机上安装 Expo Go 应用
2. 运行 `npm start`
3. 使用Expo Go扫描终端显示的二维码

## 功能说明

### 音频播放功能
当前版本使用模拟播放（2秒定时器）来演示功能。要接入真实音频：

1. 准备音频文件，放在 `assets/audio/` 目录
2. 在 `lessonsData.js` 中更新每个句子的 `audio` 字段为音频文件路径
3. 取消 `PlayerScreen.js` 中的注释代码，启用真实的音频播放功能

示例：
```javascript
sentences: [
  {
    en: 'Excuse me!',
    cn: '对不起！',
    audio: require('../../assets/audio/book1/lesson1/sentence1.mp3')
  },
]
```

### 数据管理
课文数据存储在 `src/data/lessonsData.js` 中：
- `lessonsData`: 包含四册书的所有课文和句子
- `booksInfo`: 包含四册书的基本信息

可根据实际需求修改和扩展数据。

## 待优化功能

1. **音频资源**: 集成真实的音频文件
2. **数据持久化**: 使用AsyncStorage保存用户学习进度
3. **用户系统**: 集成真实的后端API进行用户认证
4. **学习统计**: 记录详细的学习数据和进度
5. **离线支持**: 支持离线下载课程和音频
6. **主题定制**: 支持深色模式和主题切换
7. **性能优化**: 优化大列表渲染性能

## 兼容性

- **Android**: 支持 Android 5.0+
- **iOS**: 支持 iOS 12.0+
- **Web**: 支持现代浏览器

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
