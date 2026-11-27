# 灰度发布台（grayroll）

**所属领域：应用开发 · 子方向：全栈开发**

全栈产品：功能开关登记 → 环境绑定 → 人群圈选 → 灰度规则 → 发布生效 → 紧急熔断 → 单点覆盖 → 变更历史 → 在线求值。

## 骨架一句话

功能开关按环境配置灰度比例与人群，发布须版本落库才能生效，紧急熔断与变更历史同源。

## H3 切口候选（写路径互斥 · 须择一）

1. **发布生效**：同事务写入正式生效配置并升版本锁旧版，或只写影子发布草案、升正时原子落正式区（正式区升正前零改）。
2. **紧急熔断**：同事务立即写正式关闭并记变更，或影子紧急草案确认后原子熔断。
3. **人群绑定**：同事务写正式人群规则，或影子绑定草案升正。

正确性口径只能走甲乙中的一种且两边不得混用。

## 一键起环境

```bash
docker compose up -d --build
```

浏览器：http://localhost:11720

- `admin` / `admin123`（管理员）
- `writer` / `writer123`（发布员）
- `viewer` / `viewer123`（只读）

## 本地开发

```powershell
cd projects/17-grayroll
$env:PYTHONPATH="backend"
python -m uvicorn app:app --app-dir backend --reload --port 8020
python -m pytest
python scripts/count_loc.py
```

## 空桩

- 远程配置推送（`remote_push`）
- 实验平台桥接（`experiment_bridge`）

接口固定返回 501，题面可点名。
