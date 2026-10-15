# 更低成本的 iLab Conjure 多模型图片方案

[English](README.md) · [上游说明](README.upstream.md)

[ToAPIs · 对应模型价格与接入](https://go2v.toapis.com/il15gc)

**2026-10-15：4 张真实输出，图片实扣合计 $0.0544（10.88积分），后台截图已确认。**

原 OpenAIImagesAdapter → ToAPIs异步适配 → 原 GenerationResult；WebUI交互未验收。

## 演示

![真实输出与实扣](screenshots/cn/01-models.png)

## 本次对应模型价格

| Model | Requested preset | Actual pixels | Quote / request | Actual charge |
|---|---|---|---:|---|
| [`gpt-image-2-vip`](https://go2v.toapis.com/il15v) | low / 1K | 1024×1024 | $0.0019 | $0.0019 / 0.38 credits |
| [`gemini-nano-banana-2.1`](https://x.toapis.com/il15n) | 1K | 1024×1024 | $0.0150 | $0.0150 / 3 credits |
| [`gpt-image-2`](https://go.toapis.com/il15s) | 1K | 1280×1280 | $0.0150 | $0.0150 / 3 credits |
| [`gpt-image-2.5-flare`](https://im25.toapis.com/il15f) | high / 1K | 1024×1024 | $0.0225 | $0.0225 / 4.5 credits |

本次图片实扣合计： **$0.0544**. 本次图片实扣已由后台截图确认；1积分=$0.005。除 global 为用户提供价表，其余为当天实时 `/v1/pricing`。不同模型/画质不是等效质量比较。

## 复现

环境：Python 3.11及以上；Node/TS原生入口验收另需Node 22及以上。

```bash
python -m pip install Pillow
python generate_case.py --model gpt-image-2-vip --prompt "An original product photograph, no text"
# 默认演练不联网。实测前在本机私下配置 TOAPIS_API_KEY，再显式加 --live。
python generate_case.py --model gpt-image-2-vip --prompt "An original product photograph, no text" --run-id my-unique-case --output result.png --live
```

`TOAPIS_BASE_URL`可填`https://toapis.com`或`https://toapis.cn`，只补一次`/v1`。`TOAPIS_STATE_DIR`保存本地私有任务状态；`TOAPIS_MAX_IMAGE_USD`默认单图报价上限为0.10。不要提交Key或私有状态目录。

### 原生入口与范围

`codex_image/providers/openai.py` → 显式识别ToAPIs域名的分支 → `codex_image/providers/toapis.py` → 原`GenerationResult`返回类型。

`python smoke_native.py < case.json` (`model`, `prompt`; requires key). 验收使用原项目`ExecutionPlan`数据类并调用真实适配器。仅启用单张方图；蒙版、透明与未映射选项在提交前拒绝。UI模型绑定配置仍需维护者产品内验收。

### 接口映射

`POST /v1/images/generations`提交一次并保存返回任务ID，再通过`GET /v1/images/generations/{id}`查询结果。下载CDN图片时不转发API Key；Bearer仅发给允许的API域名。没有自动POST重试，未确认是否受理的提交会保留并阻止重复生成。

适配器将像素提示转换为画幅比例，并按模型发送分辨率字段。JPEG结果保留原始字节，另存PNG供展示；真实尺寸均写入记录。请求1K不保证返回恰好1024×1024。

## 证据与截图教程

- [逐任务记录](evidence/)
- [原始输出](examples/)
- [模型对比](screenshots/cn/01-models.png)
- [API调用步骤](screenshots/cn/02-api.png)
- [复用与验收边界](screenshots/cn/03-reuse.png)

Upstream: [kadevin/ilab-conjure](https://github.com/kadevin/ilab-conjure/tree/049f105c49c267ccddcabd899ecc503c5c184ae3), pinned `049f105c49c267ccddcabd899ecc503c5c184ae3`. 社区独立示例，不代表作者背书或已有合作。[署名与许可](NOTICE.md)。

[后台确认的逐项图片消费](evidence/actual-charges.json)。未取得任务ID的视频提交不计入图片合计，仍单独待核。
