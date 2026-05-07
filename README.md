# PulseFit KnowAgent

这是为了飞书的一个比赛而做的项目。

为了能够启动，你需要一个能够连接飞书 bot 的 OpenClaw agent，并将下方目录中的文件替换到你的 OpenClaw agent 的 workspace 中。

```text
.
├── LICENSE
├── README.md
└── workspace/          # 包含本项目 workspace 中所需替换的文件
    ├── AGENTS.md       # 可直接替换
    ├── SOUL.md         # 可直接替换
    └── skills/         # 可直接替换
```

同时，你也需要给飞书 bot 一些授权，但我想 OpenClaw 足够聪明，会指导你配置的。

建议你在本地部署的时候，扫描一下 skills/ 路径下的文件，看看需要配置什么内容。