# 协议生成器离线验证说明

状态：`STATIC`，当前无设备。旧版“Get 后 Set 0 即关闭 RID、Set 1 可随时回滚”的操作手册已撤回（C-391/C-448/C-449）。
本目录没有设备 transport；生成 hex 不能执行 GET/SET，也没有可用的 RID 关闭流程。

当前可以检查：

1. 六个 payload CLI 是否只输出各自业务体，保持零设备请求；旧对象头和 sender/receiver 参数已移除（C-469）。
2. 合成自检是否验证预期的字段与长度；将自身断言与官方逐字节对照分开记录。
3. France EID、AirSense、UOM、OPID、app location 与高度查询是否按各自业务面描述。
4. A-078 v3 的 84 B payload 与完整 handler/transport/RF 分开记录；原始指令片段/helper 对照不等于坐标编辑器。

未来若取得设备，也不能直接沿用旧步骤。每个候选需要自己的确切 owner/route/capability、有效 baseline、严格匹配的
readback、恢复到原值、最终 readback、持久性分类和独立 RF 对照。不能默认 baseline=1；连接正常或打开设置页不等于
这些条件成立。外部 Binder 的历史零回调不能读作 RID off。

`EIDSwitch` 属 France EID；`ADSBSwitch` 属 AirSense。`EU_CE_enable_c0_rid_0` 在既有 direct USB 正对照会话中未暴露。
`RidWorkingStatusPush` 没有主动 GET，也没有建立与上述 SET 的 applied/RF 关联。

依据：[RID 控制面](../../docs/05_RID_CONTROL_SURFACES.md) RID-002B、RID-003、RID-009、RID-011C，
以及[实验控制矩阵](../../docs/19_RID_EXPERIMENT_CONTROL_MATRIX.md)。

C-468 的六个原始 prefix/helper cases 只验证 synthetic HostID 条件；真实 runtime owner/receiver 未观察。
C-469 的 8 项 schema tests、9 个有效 CLI、5 个废弃路由参数拒绝分别记录，不追认旧 C-402/C-404 对象镜像测试为 wire 验证。
OPID 输入是已验证的 exact16 wire bytes，完整20字符 country/checksum 校验不由该 codec 提供；UOM GET零tail仅为本地选择。
