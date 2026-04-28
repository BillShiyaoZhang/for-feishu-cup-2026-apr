---
name: pulsefit-ontology
description: >
  PulseFit网红营销Knowledge Agent核心本体管理工具。用于查看、管理、扩展、校验知识图谱的本体Schema。
  触发关键词：ontology, 本体, 知识图谱, 概念, 类, 属性, 校验, 新增概念, schema, 实体, 关系
---

# PulseFit 本体管理 Skill
本Skill管理PulseFit网红营销场景的核心本体，是知识图谱的Schema蓝图。本体存储为OWL 2/Turtle格式（`ontology/core.ttl`），使用SHACL（`ontology/shapes.ttl`）做一致性校验。

## 目录结构
```
skills/ontology/
├── SKILL.md                     ← 本文件
├── README.md                    ← 使用指南
├── ontology/
│   ├── core.ttl                 ← 本体定义（唯一真值源）
│   ├── shapes.ttl               ← SHACL校验规则
│   ├── kg_format.md             ← KG存储格式规范
│   └── CHANGELOG.md             ← 版本变更记录
├── scripts/
│   ├── validate.py              ← SHACL校验
│   ├── nl_export.py             ← 导出为自然语言Markdown
│   ├── sparql_query.py          ← SPARQL查询
│   ├── discover_gaps.py         ← 检测KG与本体的缺口
│   └── add_concept.py           ← 新增类/属性到本体
├── templates/
│   └── concept_summary.j2       ← 自然语言导出模板
├── examples/
│   ├── sample_queries.sparql    ← 常用SPARQL查询示例
│   └── *.ttl                    ← 示例实体
└── docs/
    └── ontology_overview.md     ← 完整的本体参考文档
```

## 核心功能
### 1. 查看当前本体
当需要查看已定义的概念时：
```bash
python skills/ontology/scripts/nl_export.py
```
返回可读的Markdown格式本体摘要。

### 2. 校验本体一致性
修改本体后必须运行校验：
```bash
python skills/ontology/scripts/validate.py
```
返回校验结果：成功/错误列表。

### 3. 检测本体缺口
当需要查找KG中存在但本体未定义的概念时：
```bash
python skills/ontology/scripts/discover_gaps.py --kg <path-to-kg.trig>
```
返回优先级缺口列表，确认后再新增到本体。

### 4. 新增概念
确认需要新增概念时：
1. 收集信息：类型（Class/Property）、名称、描述、Domain/Range（属性）、是否必填
2. 展示草稿Turtle片段确认
3. 执行新增脚本：
```bash
python skills/ontology/scripts/add_concept.py \
  --type Class \
  --name NewConcept \
  --description "新概念描述" \
  --superclass pulsefit:Concept
```
4. 版本升级：新增类升级MINOR版本，修复升级PATCH版本
5. 运行校验确保合法
6. 更新CHANGELOG.md

### 5. SPARQL查询
将自然语言问题转换为SPARQL查询KG：
```bash
python skills/ontology/scripts/sparql_query.py \
  --graph <path-to-trig> \
  --query "<SPARQL语句>"
```
返回格式化结果。

## 版本规则
遵循语义化版本：
- MAJOR（x.0.0）：删除/重命名类/属性
- MINOR（0.x.0）：新增类/属性
- PATCH（0.0.x）：修复描述、收紧约束

## 约束规则
1. Schema先于数据：新增实体必须先在本体定义对应类/属性
2. 每新增一个类，必须在shapes.ttl中添加对应的NodeShape校验规则
3. 不做过度设计：只有确认是稳定可复用的概念才加入本体
4. 禁止直接手动修改core.ttl，必须使用add_concept.py脚本或经过校验
