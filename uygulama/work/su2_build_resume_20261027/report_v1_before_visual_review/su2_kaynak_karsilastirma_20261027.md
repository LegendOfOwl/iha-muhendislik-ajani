# SU2 kaynak derlemesi ve kontrollü karşılaştırma

27 Ekim2026 · Üç yeni native CFD koşusu · Genel fizik kabulü: **false**.

SU2 kaynak32 derlemesi, korunmuş başarısız denemeden 258 doğrulanmış nesneyi kullanarak kalan 32 hedefi 81.063 saniyede tamamladı. Üç yeni native CFD koşusu aynı kaynak ağ ve başlangıçla 200 adım çalıştı. Resmî release32–kaynak32 yeniden üretimi geçti: beş SI log10 RMS eğrisindeki en büyük fark 0.00175396, son CD mutlak farkı 0. Yalnız MAX_LINELET_POINTS=32→256 değiştirildi. Yoğunluk kazancı -0.00938603 log10, SA kötüleşmesi -0.00099585 log10, Krylov sayımı oranı 1.00000000, bu çiftte gözlenen süre oranı 1.28308938; ön kayıtlı ortak etki/maliyet kabulü geçmedi. 40 yeni yazılım kontrolü geçti; eski70 kontrol yeni sayılmadı. Krylov sayımı işlem maliyetinin vekilidir; daha uzun çizgilerin eşit aritmetik maliyeti olduğu veya tek çiftin evrensel hız kıyası olduğu iddia edilmez. Genel fizik/RAE2822/M6/İHA kabulleri açık; LLM davranışında iyileşme ölçülmedi.

## Derlemede ne değişti?

Önceki `p32a` başarısız kaydı başarısız kaldı; `p32b` bellek korumasının native başlamadan verdiği ret de korundu. Yeni `p32r`, kaynak baytlarına dokunmadan yalnız sorunlu CFlowTractionInterface.cpp derleme birimine kayıtlı başlık arama argümanını ekledi. 290 etkin komutun 289 tanesi değişmedi; 258 nesnenin hash’i yeniden denetlendi ve kalan 32 hedef 81.063s sürdü. Önceki başarısız aşamayla kümülatif native süre 661.938s. Daha önce önerilen global cpp_args seçeneği bu kurtarma derlemesine taşınmadı. `p32r/source` gerçek derleme yolunun bayt eşdeğer arşividir; asıl derleme p32a çalışma ağacında yapılmış, EXE sonra p32r kaydına kopyalanmıştır.

Kaynak256 yeni klasörde, nesne önbelleği taşınmadan derlendi. Aynı genişletilmiş derleyici/linker/archive/Python/Ninja manifesti, runtime DLL kimliği ve etkin komutlar doğrulandı; kaynakta yalnız `MAX_LINELET_POINTS=32→256` farkı var. Bu, tüm işletim sistemi/SDK ortamının veya bağımsız bir temiz oda derlemesinin eşdeğerliği değildir.

## Kaynak32 resmî sonucu yeniden üretiyor mu?

| SI log10 RMS bileşeni | Bütün200 adımda en büyük mutlak fark | Ön kayıtlı üst sınır |
|---|---|---|
| Rho | 4.468e-05 | 0.03 |
| RhoU | 1.57e-05 | 0.03 |
| RhoV | 0.00078723 | 0.03 |
| RhoE | 0.00175396 | 0.03 |
| nu | 4.292e-05 | 0.03 |

Yeniden üretim **true**. Son |ΔCD|=0; toplam akış+SA Krylov sayımı 16000→16000; native boolean üyelik aynı. Bu sayısal ekran, farklı GNU/runtime derlemeleri arasında bu vaka için işlemsel eşdeğerlik kanıtıdır; fizik hata bandı değildir.

## Tek kaynak değişikliğinin etkisi

| Kayıt | Son SI yoğunluk log10 RMS | Son SI SA log10 RMS | CD | Son100 CD aralığı | Krylov sayımı | Süre,s | Native üye | Logdaki ortalama çizgi noktası | Aynı eski RHS yoğunluk kare payı |
|---|---|---|---|---|---|---|---|---|---|
| Resmî release32 | -9.761678858 | -12.244438015 | 0.002848056245 | 1.394e-09 | 16000 | 82.656 | 7200 | 32 | %53.896527 |
| Kaynak32 | -9.761658478 | -12.244457275 | 0.002848056245 | 1.394e-09 | 16000 | 74.125 | 7200 | 32 | %53.896527 |
| Kaynak256 | -9.752272448 | -12.245453125 | 0.002848056217 | 1.408e-09 | 16000 | 95.109 | 34401 | 152 | %99.979010 |

Ortalama çizgi noktası yalnız native logun tam `Computed linelet structure, ... points in each line (average).` satırından okunur. Yazdırılmış ortalama, tek tek çizgi boylarının dağılımı veya her çizginin cap değerine ulaştığı anlamına gelmez; yeni kabul kapısı değildir.

| Ön kayıtlı kapı | Gerçek durum |
|---|---|
| `valid_contract` | true |
| `build32_normalization` | true |
| `build32_native_exit_and_matched_iteration` | true |
| `build32_complete_finite_history` | true |
| `build32_complete_stable_CD_window` | true |
| `build32_field_validity_proven` | true |
| `build32_positive_finite_elapsed` | true |
| `build32_bijective_native_mapping` | true |
| `build32_canonical_native_membership` | true |
| `build32_input_identities_present` | true |
| `build256_normalization` | true |
| `build256_native_exit_and_matched_iteration` | true |
| `build256_complete_finite_history` | true |
| `build256_complete_stable_CD_window` | true |
| `build256_field_validity_proven` | true |
| `build256_positive_finite_elapsed` | true |
| `build256_bijective_native_mapping` | true |
| `build256_canonical_native_membership` | true |
| `build256_input_identities_present` | true |
| `pristine_reproduction_passed_for_same_baseline` | true |
| `shared_input_identities` | true |
| `compiler_options_identity` | true |
| `runtime_dependencies_identity` | true |
| `only_registered_source_cap_change` | true |
| `density_gain` | false |
| `SA_worsening` | true |
| `combined_Krylov_cost` | true |
| `observed_elapsed_cost` | true |
| `same_fixed_old_RHS` | true |
| `native_membership_nodes_increased` | true |
| `fixed_RHS_Rho_share_increased` | true |

Ortak kabul **false**. Yoğunluk kazancı -0.009386030 (hedef≥0.3); SA kötüleşmesi -0.000995850 (hedef≤0.1); Krylov sayımı oranı 1.000000000 (üst sınır 1.5); gözlenen süre oranı 1.283089376 (üst sınır 1.5). Eşikler değişmedi; bütün gerekli kapılar birlikte değerlendirildi. Krylov sayımı aritmetik işin yalnız vekilidir: çizgi boyu değişince bir iterasyonun maliyeti eşit kabul edilmez. Gerçek süre bu yüzden ayrı verildi; tek eş koşu çifti genel performans oranı değildir. Bu vakada kaynak32 sayımı 16000=200×(40+40) ile kayıtlı toplam tavanın tamamı olduğundan, aynı tavanlı aday için Krylov≤1,5 oran kapısı ayırt edici değildir; eşik değiştirilmedi ve gerçek süre ayrı değerlendirildi.

## İç doğrusal çözümler: ek gözlem, yeni kabul eşiği yok

| Kayıt | Akış / SA40-tavanına ulaşma | Son LinSolRes ham log10 | Son LinSolResTurb ham log10 |
|---|---|---|---|
| Resmî release32 | 200/200 · 200/200 | -0.922353669 | -2.705025871 |
| Kaynak32 | 200/200 · 200/200 | -0.922598246 | -2.697869215 |
| Kaynak256 | 200/200 · 200/200 | -2.574917083 | -2.730073032 |

Bu sütunlar CSV’den doğrudan okunan iç doğrusal çözücü artıklarıdır; yukarıdaki beş SI nonlinear RMS eğrisiyle aynı nicelik değildir. Bu FGMRES yolunda döndürülen değer `beta/norm0` olup beta, Givens döndürmeleri sonrası azaltılmış sistemin `g[i+1]` değerinden güncellenir. Dolayısıyla LinSolRes burada bağımsız olarak yeniden hesaplanmış `||Ax-b||` ölçümü diye sunulmaz. norm0 önce `||b||` olur; bağıl toleransta başlangıç artık normuna ayarlanır. Gerçek `mat_vec(x)-b` yeniden hesabı, kaynakta yalnız monitoring/COMM_FULL ve recomputeRes koşullu dalındadır; bu dal döndürülen `beta/norm0` değerinin yerine geçmez. [Sabit kaynak: CSysSolve.cpp468–616](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/Common/src/linear_algebra/CSysSolve.cpp#L468-L616). İterasyon sayılarının tavanı görmesi, tek başına hassasiyet veya fizik kabulü kanıtı değildir. Bu gözlem için sonuçtan sonra yeni geçme/kalma kapısı eklenmedi.

![Üç koşunun beş SI geçmişi ve CD](../plots/su2_kaynak_karsilastirma_20261027_history.png)

## Çizgi kapsamının konumu

Boolean üyelik native Linelet alanının pozitifliğinden gelir; graph renkleri çizgiID değildir. Kapsanan pay, bütün kollarda aynı dondurulmuş eski sıralı akış/SA aşama RHS’sinin yoğunluk kare toplamıdır. Yeni implicit alanların yeniden hesaplanmış nonlinear artığı, nedensel hata haritası veya ağ hata bandı değildir.

![Tam alan ve yakın görünümde gerçek üyelik](../plots/su2_kaynak_karsilastirma_20261027_membership.png)

Bütün **52689 düğüm**, dışarıda kalanlar dahil [konum/üyelik CSV’sinde](../data/qualification/linecap_source_20261027_v1/all_nodes_membership.csv) korunur. Yakın görünüm yalnız eksen sınırını değiştirir; dışındaki düğümler silinmez.

## Korunan kayıtlar ve sınırlar

İki eski düz plaka ailesinin 738 ham hash kaydı ve yeni üç kolun 45 kaydı eşleşti. Donmuş/canlı native kod, CASE sözleşme çapası, kaynak ağaçları, tek yama, derleyici/runtime ve EXE mühürleri yeniden denetlendi. 40 yeni kontrolün dağılımı: 28 derleme/yöntem ve 12 yayın koruması. Eski70 kontrol bu sayıya eklenmedi.

Nesne-cache ek çapraz denetiminde Windows/posix yol ayracı nedeniyle KeyError görüldü; normalize edilmiş yeniden denetim geçti. Bu sırada tek mevcut derleme işi sürdü; ikinci native iş başlatılmadı. Davranış riski, bağımlı ek denetimin dönüş koduna bakmadan işi başlatmaktı; dosyadaki çıkarım ve düzeltme korunuyor. Bu bir süreç olayıdır, CFD’nin fiziksel hata nedeni veya LLM iyileşme kanıtı değildir.

Eski fine3999 rolü ve üç-ağ ailesi korunur; bu üç200-adımlık mekanizma kolu onların yerine seçilmez. Ağ, uzak alan, deney ve bağımsız fizik kabulleri kapanmadı; GCI üretilmedi. Bu kaynak benchmarkı keyfiCAD→CFD/İHA hizmeti, stall/3B M6 yeterliliği veya uzman LLM kanıtı değildir.

- [Bütün sonuç ve dosya mühürleri](su2_kaynak_karsilastirma_20261027.json)
- [Yeni40 yazılım kontrolü](su2_resume_checks_20261027.json)
- [Önceki kaynak hazırlığı](su2_kaynak_kontrolu_20261027.html)
- [Native sözleşme](../simulations/linecap_source_20261027_v1/contract.json)
- [Kaynak değişikliği](../simulations/linecap_source_20261027_v1/source_change.json)
- [Kayıtlı etki kararı](../simulations/linecap_source_20261027_v1/effect.json)

Kaynak kimliği: [sabit SU2 v8.5.0 commit](https://github.com/su2code/SU2/tree/12eb826f049ef7f67df974dfcb44cf36ee07c0f8). Yeni üçüncü taraf bağımlılık kurulmadı; rapor mevcut matplotlib ve standart HTML araçlarıyla üretildi.
