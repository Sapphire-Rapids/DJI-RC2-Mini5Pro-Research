# DJI Fly 1.21.10 runtime route exact ELF manifest

日期：2026-08-28
状态：**离线、只读、exact-build；没有连接或操作设备**

## 作用

`runtime_route_manifest_20260828.json` 是 EID/RID route resolver 的失败关闭准入清单。
生成器只使用 Python 标准库，不读取 ELF section header。它按 `PT_DYNAMIC.p_vaddr`
经唯一、file-backed `PT_LOAD` 映射到真实 dynamic table，再从 `DT_GNU_HASH` 的
bucket/chain 推导 dynsym 数量。这样不会被 DJI 样本中误导性的
`PT_DYNAMIC.p_offset` 或损坏的 section table 带偏。

## 精确模块

| 模块 | bytes | SHA-256 | GNU build-id | dynsym | dynamic claimed → mapped |
| --- | ---: | --- | --- | ---: | --- |
| `libsdk_jni.so` | 87313856 | `5abd990c86bcd00c9a652a21e329ad4580a20ec9f80188075ada61f5a7b46286` | `c892b3c06664df91d643f84ae9e59a906387068b` | 78496 | `0x5344ae0` → `0x5221d10` |
| `libsdk_key_value.so` | 12684576 | `09f4aa8aef65f720da09a1dad79c8851e05d619affaf73708bf6747341208336` | `877a01a5b4b17e0a0f1b9153ccfe24891fb3c230` | 51801 | `0xc18ae0` → `0xc04cc0` |
| `libsdk_base.so` | 7720240 | `e5b290ebc6aa6e409e116cc0d3b84fb4e49c70f6c552feffacd5b15c7c83e873` | `de104ddaca91438807b21688baf08455d5ade20c` | 14944 | `0x75cae0` → `0x717500` |

## 固定目标

函数记录 dynsym index/bind/type/visibility/shndx/RVA/size、所在 segment，以及入口
最多 16 bytes（短函数取完整 4/8/12 bytes）的精确 AArch64 签名。全局对象与 vtable
只记录 segment、RVA 和合法
address point；它们可能位于 BSS 或含运行时 relocation，故**不对 file bytes 做错误哈希**。

### `libsdk_jni.so`

| role | dynsym | attr | RVA | size | segment | admission evidence |
| --- | --- | --- | ---: | ---: | --- | --- |
| `module_mediator_singleton_slot` | `_ZN3uav3sdk17g_pModuleMediatorE` (#65107) | GLOBAL/OBJECT/DEFAULT/shndx=23 | `0x5344600` | 8 | #2 RW- zero_fill_bss | address-only |
| `get_instance_do_not_call` | `_ZN3uav3sdk11GetInstanceEv` (#4858) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d3ae40` | 140 | #0 R-X file_backed | entry16 `fd7bbea9f44f01a9fd03009154a701b0` |
| `get_framework_core_weak_owner` | `_ZN3uav3sdk14ModuleMediator16GetFrameworkCoreEv` (#64131) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d54ff8` | 56 | #0 R-X file_backed | entry16 `091842f9690100b4090100f9091c42f9` |
| `get_product_manager_shared_owner` | `_ZN3uav3sdk14ModuleMediator13GetProductMgrEv` (#46775) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d54da0` | 56 | #0 R-X file_backed | entry16 `091042f9690100b4090100f9091442f9` |
| `module_mediator_get_worker` | `_ZN3uav3sdk14ModuleMediator9GetWorkerEv` (#77526) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d55030` | 56 | #0 R-X file_backed | entry16 `09f841f9690100b4090100f909fc41f9` |
| `module_mediator_run_on_work_thread` | `_ZN3uav3sdk14ModuleMediator15RunOnWorkThreadENSt6__ndk18functionIFvvEEEb` (#29569) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d55764` | 720 | #0 R-X file_backed | entry16 `ff4307d1fd7b19a9fc5f1aa9f6571ba9` |
| `framework_core_get_worker` | `_ZNK3uav3sdk16SDKFrameworkCore9GetWorkerEv` (#6855) | WEAK/FUNC/DEFAULT/shndx=14 | `0x2501904` | 40 | #0 R-X file_backed | entry16 `0a0440f9090840f90a2500a9c90000b4` |
| `framework_core_get_semantic_key` | `_ZN3uav3sdk16SDKFrameworkCore6GetKeyEjjjjjRKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE` (#54849) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25006bc` | 52 | #0 R-X file_backed | entry16 `29690190290940f9e00308aa29014079` |
| `hardware_layer_get_abstraction` | `_ZN3uav3sdk13HardwareLayer14GetAbstractionERKNSt6__ndk16vectorIjNS2_9allocatorIjEEEE` (#4078) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x250d6c0` | 8 | #0 R-X file_backed | entry8 `00800091af8aad14` |
| `base_abstraction_get_characteristics_by_cache_key` | `_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNS0_8CacheKeyE` (#12314) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x2515d94` | 52 | #0 R-X file_backed | entry16 `fd7bbea9f30b00f9fd030091f30300aa` |
| `base_abstraction_get_characteristics_by_string` | `_ZN3uav3sdk15BaseAbstraction18GetCharacteristicsERKNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE` (#19431) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25195e4` | 440 | #0 R-X file_backed | entry16 `ff0301d1fd7b02a9f44f03a9fd830091` |
| `base_abstraction_get_abstraction_key` | `_ZN3uav3sdk15BaseAbstraction17GetAbstractionKeyEv` (#65581) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25194f0` | 228 | #0 R-X file_backed | entry16 `ff4301d1fd7b02a9f51b00f9f44f04a9` |
| `base_abstraction_get_datalink_id` | `_ZNK3uav3sdk15BaseAbstraction13GetDataLinkIDEv` (#52584) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25194bc` | 12 | #0 R-X file_backed | entry12 `01c00291e00308aa1f09ad14` |
| `base_abstraction_get_device_id` | `_ZNK3uav3sdk15BaseAbstraction11GetDeviceIDEv` (#55804) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25194c8` | 8 | #0 R-X file_backed | entry8 `00e040b9c0035fd6` |
| `base_abstraction_get_product_id` | `_ZNK3uav3sdk15BaseAbstraction12GetProductIDEv` (#74448) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25194d0` | 8 | #0 R-X file_backed | entry8 `009840b9c0035fd6` |
| `base_abstraction_get_abstraction_id` | `_ZNK3uav3sdk15BaseAbstraction16GetAbstractionIDEv` (#18742) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25194d8` | 8 | #0 R-X file_backed | entry8 `00a040b9c0035fd6` |
| `base_abstraction_get_sender_seq_diagnostic_only` | `_ZNK3uav3sdk15BaseAbstraction12GetSenderSeqEv` (#18461) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x25195dc` | 8 | #0 R-X file_backed | entry8 `00a04339c0035fd6` |
| `base_abstraction_get_component_index` | `_ZNK3uav3sdk15BaseAbstraction17GetComponentIndexEv` (#27058) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x2519b10` | 8 | #0 R-X file_backed | entry8 `00e440b9c0035fd6` |
| `product_manager_get_datalink_by_product_id` | `_ZN3uav3sdk10ProductMgr22GetDatalinkByProductIdEjRNSt6__ndk112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEERt` (#9604) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x24fcd2c` | 308 | #0 R-X file_backed | entry16 `fd7bbba9f90b00f9f85f02a9f65703a9` |
| `module_mediator_add_product_connection_observer` | `_ZN3uav3sdk14ModuleMediator28AddProductConnectionObserverENSt6__ndk18functionIFvjRKNS0_11ProductInfoEEEENS3_IFvjEEE` (#30675) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d5b508` | 1720 | #0 R-X file_backed | entry16 `fd7bbca9fc5f01a9f65702a9f44f03a9` |
| `module_mediator_remove_product_connection_observer` | `_ZN3uav3sdk14ModuleMediator31RemoveProductConnectionObserverEm` (#59285) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d5bbc0` | 704 | #0 R-X file_backed | entry16 `fd7bbca9fc0b00f9f65702a9f44f03a9` |
| `module_mediator_add_datalink_observer` | `_ZN3uav3sdk14ModuleMediator19AddDatalinkObserverENSt6__ndk18functionIFvRKNS2_12basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEEEEESD_` (#60876) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d550a0` | 1732 | #0 R-X file_backed | entry16 `fd7bbca9fc5f01a9f65702a9f44f03a9` |
| `module_mediator_remove_datalink_observer` | `_ZN3uav3sdk14ModuleMediator22RemoveDatalinkObserverEm` (#13888) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d55a34` | 724 | #0 R-X file_backed | entry16 `fd7bbca9fc0b00f9f65702a9f44f03a9` |
| `product_manager_add_product_connection_observer` | `_ZN3uav3sdk10ProductMgr28AddProductConnectionObserverEmNSt6__ndk18functionIFvjRKNS0_11ProductInfoEEEENS3_IFvjEEE` (#76776) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x24fca3c` | 676 | #0 R-X file_backed | entry16 `ff8302d1fd7b06a9f73b00f9f65708a9` |
| `product_manager_remove_product_connection_observer` | `_ZN3uav3sdk10ProductMgr31RemoveProductConnectionObserverEm` (#72878) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x24fcce0` | 76 | #0 R-X file_backed | entry16 `e90300aa2a8d4af8ca0100b4e80301aa` |
| `target_shared_weak_lock` | `_ZNSt6__ndk119__shared_weak_count4lockEv` (#24541) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d2f300` | 84 | #0 R-X file_backed | entry16 `5f2403d5082000910afddfc85f0500b1` |
| `target_release_shared` | `_ZNSt6__ndk119__shared_weak_count16__release_sharedEv` (#77553) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d2f244` | 136 | #0 R-X file_backed | entry16 `3f2303d5fd7bbea9f44f01a9fd030091` |
| `target_release_weak` | `_ZNSt6__ndk119__shared_weak_count14__release_weakEv` (#63352) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x1d2f2cc` | 52 | #0 R-X file_backed | entry16 `5f2403d50840009109fddfc8e90000b4` |
| `target_string_init` | `_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEE6__initEPKcm` (#6239) | WEAK/FUNC/DEFAULT/shndx=14 | `0x1d30ee8` | 144 | #0 R-X file_backed | entry16 `3f2303d5fd7bbda9f65701a9f44f02a9` |
| `target_string_dtor` | `_ZNSt6__ndk112basic_stringIcNS_11char_traitsIcEENS_9allocatorIcEEED2Ev` (#67996) | WEAK/FUNC/DEFAULT/shndx=14 | `0x1d30bcc` | 24 | #0 R-X file_backed | entry16 `5f2403d50800403948000037c0035fd6` |
| `target_cache_key_dtor` | `_ZN3uav3sdk8CacheKeyD2Ev` (#5244) | WEAK/FUNC/DEFAULT/shndx=14 | `0x4a32a48` | 68 | #0 R-X file_backed | entry16 `fd7bbea9f30b00f9fd030091f30300aa` |
| `vtable_hardware_layer` | `_ZTVN3uav3sdk13HardwareLayerE` (#44996) | GLOBAL/OBJECT/DEFAULT/shndx=16 | `0x50f1250` | 120 | #1 RW- file_backed | address-points `0x50f1260`, `0x50f12b8` |
| `vtable_abstraction_manager_impl` | `_ZTVN3uav3sdk22AbstractionManagerImplE` (#46945) | GLOBAL/OBJECT/DEFAULT/shndx=16 | `0x50f2040` | 408 | #1 RW- file_backed | address-points `0x50f2050` |
| `vtable_product139_fc_mixabs` | `_ZTVN3uav3sdk3key6MixAbsINS0_32UAV77FlightControllerAbstractionENS1_11UAV139FCAbsEEE` (#14021) | WEAK/OBJECT/DEFAULT/shndx=16 | `0x5100f88` | 1584 | #1 RW- file_backed | address-points `0x5100f98` |

### `libsdk_key_value.so`

| role | dynsym | attr | RVA | size | segment | admission evidence |
| --- | --- | --- | ---: | ---: | --- | --- |
| `cache_key_get_prefixes` | `_ZNK3uav3sdk8CacheKey11GetPrefixesEv` (#22886) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x7eab64` | 8 | #0 R-X file_backed | entry8 `00c00091c0035fd6` |
| `characteristics_get_extra_param` | `_ZNK3uav3sdk15Characteristics13GetExtraParamEv` (#25465) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x8f9a54` | 276 | #0 R-X file_backed | entry16 `ff0307d1fd7b1aa9fc4f1ba9fd830691` |
| `extra_param_get_single_send_pack_host_id` | `_ZNK3uav3sdk25CharacteristicsExtraParam17GetSendPackHostIDEv` (#35309) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x8f9bb0` | 4 | #0 R-X file_backed | entry4 `c0035fd6` |
| `extra_param_get_send_pack_host_ids` | `_ZNK3uav3sdk25CharacteristicsExtraParam18GetSendPackHostIDsEv` (#49658) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x8f9bec` | 8 | #0 R-X file_backed | entry8 `00200091c0035fd6` |
| `characteristics_invalid_singleton` | `_ZN3uav3sdk15Characteristics7InvalidE` (#44958) | GLOBAL/OBJECT/DEFAULT/shndx=23 | `0xc19d78` | 56 | #2 RW- zero_fill_bss | address-only |

### `libsdk_base.so`

| role | dynsym | attr | RVA | size | segment | admission evidence |
| --- | --- | --- | ---: | ---: | --- | --- |
| `global_packet_status_instance` | `_ZN3uav4core18GlobalPacketStatus8instanceEv` (#2175) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x2ec280` | 168 | #0 R-X file_backed | entry16 `fd7bbea9f44f01a9fd03009188230090` |
| `global_packet_status_get_sender_index` | `_ZN3uav4core18GlobalPacketStatus20GetGlobalSenderIndexEv` (#13137) | GLOBAL/FUNC/DEFAULT/shndx=14 | `0x2ec328` | 24 | #0 R-X file_backed | entry16 `080040f9680000b400fddf08c0035fd6` |

`base_abstraction_get_sender_seq_diagnostic_only` 的 role 名称是有意的撤回标记：旧结论曾把
`BaseAbstraction::GetSenderSeq()` 当成 raw sender index；该解释错误。运行时 tuple 的
`senderIndex` 只能取本节 `GlobalPacketStatus::GetGlobalSenderIndex()`，前者不得参与发包参数。

## 校验

```sh
python3 runtime_route_manifest_20260828.py --verify
python3 runtime_route_manifest_20260828.py --self-test
```

`--verify` 会重新读取三个 whole file，并精确比较 committed JSON 的全部字段；任何
文件 hash、build-id、dynamic pointer、GNU-hash 派生计数、符号属性/RVA、segment、
代码签名或 address point 漂移都会非零退出。`--self-test` 会逐个篡改真实函数入口样本，
分别确认 whole-file SHA 与独立代码签名都会拒绝；同时确认至少一个样本的
declared dynamic offset 确实与 loader-style 映射不同。

## 运行时消费门禁

本清单不能替代进程内加载状态检查。resolver 必须只对已经加载的精确 SO 使用
`RTLD_NOLOAD` handle；禁止 plain `dlopen` 加载第二份，禁止 `RTLD_DEFAULT`。每个
`dlsym(handle, mangled)` 结果随后都要通过 `dladdr` 证明属于唯一的预期 mapping，
且地址严格等于 `load_bias + manifest RVA`。这条规则同样适用于 WEAK string/dtor/
vtable 符号；发生 interposition 时必须中止。

`RunOnWorkThread` / `GetWorker` 保留在 manifest 中用于路线审计和未来准入，并不
表示 v2.1 route-only resolver 要直接调用它们。worker 队列不是同步或 epoch barrier；
相关结论以仓库的 [evidence register](../../docs/02_EVIDENCE_REGISTER.md) 为准；
本源码目录不复制工作区审计文档。

该清单只证明当前 DJI Fly 1.21.10 的 ELF/runtime admission 条件，不证明任意其他
Fly 版本 ABI 兼容，也不调用 GET、SET、listener、transport 或设备接口。
