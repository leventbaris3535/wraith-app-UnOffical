# wraith-v2-keyboard-app (Unofficial)

> ⚠️ **Gayriresmî Proje Uyarısı**  
> Bu uygulama bir **Wraith** uygulamasıdır; ancak **Wraith’in resmi geliştiricileri tarafından geliştirilmemiştir**.  
> Resmî bir uygulama değildir ve Wraith ile herhangi bir resmî bağlantısı yoktur.

---

## 📌 Proje Hakkında

**wraith-v2-keyboard-app**, Wraith klavye uygulamasının **topluluk tarafından geliştirilmiş (unofficial)** bir masaüstü sürümüdür.

Bu projede kullanıcılar:

- Uygulamayı **kendileri exe hâline getirebilir**
- Ya da **hazır derlenmiş sürümleri** indirip kullanabilir

Hazır sürümler:

- **Kurulan sürüm (Installer)**
- **Taşınabilir sürüm (Portable)**

olarak sunulmaktadır.

---

## 🚀 Kurulum ve Kullanım

Uygulamayı kullanmak için iki farklı yol bulunmaktadır.

---

## 🔧 1. Kaynaktan Kurulum  
### (EXE Oluşturmak İsteyenler İçin)

Bu proje, **build.bat** dosyası sayesinde **hiçbir manuel komut girmeden** otomatik olarak exe oluşturabilir.

### Gereksinimler

- **Windows**
- **Node.js** (LTS sürümü önerilir)  
  👉 https://nodejs.org
- İnternet bağlantısı (ilk kurulum için)

---

### ⚙️ EXE Oluşturma (Önerilen Yöntem)

1. Bu repository’deki **tüm dosyaları indirin** veya projeyi klonlayın  
2. Proje klasöründe bulunan **build.bat** dosyasına **çift tıklayın**  
3. Gerekirse Windows sizden **Yönetici izni** isteyecektir (otomatik olarak)  
4. Script otomatik olarak:
   - `npm install` çalıştırır
   - `npm run dist` ile build alır
5. İşlem tamamlandığında **exe dosyanız oluşturulur**

🟢 Ekstra komut girmenize gerek yoktur  
🟢 Tüm işlemler otomatik yapılır  

---

### ℹ️ build.bat Ne Yapar?

`build.bat` dosyası:

- Yönetici yetkisini kontrol eder  
- Doğru proje dizinine geçer  
- Gerekli npm paketlerini kurar  
- Build (exe) işlemini başlatır  
- Başarılı veya hatalı durumu kullanıcıya bildirir  

Başarılı olursa:
