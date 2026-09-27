"""Real Turkish test texts for timed practice — 3 difficulty levels, 20 each."""
from __future__ import annotations

import random

EASY_TEXTS = [
    "Merhaba dünya. Bugün hava çok güzel. Güneş parlıyor ve kuşlar şarkı söylüyor.",
    "Sabah kahvaltısı yapmayı severim. Çay içerim, ekmek yerim. Bazen peynir de yerim.",
    "Kediler çok sevimli hayvanlardır. Uzun kuyrukları vardır. Süt içmeyi çok severler.",
    "Kitap okumak güzel bir alışkanlıktır. Her gün biraz okumak zihni açık tutar.",
    "Parkta çocuklar oynuyor. Anneler banklarda oturuyor. Hava sıcak ve güneşli.",
    "Arabamız mavi renk. Babam sürüyor. Ben arka koltukta oturuyorum. Pencerden bakıyorum.",
    "Okula sabah gidiyorum. Dersler ilginç. Öğretmenimiz çok iyi anlatıyor.",
    "Elma kırmızı, muz sarı, üzüm mor. Meyveler sağlıklı ve lezzetlidir.",
    "Bisiklet sürmek eğlencelidir. Dengede kalmak gerekir. Pedalları çevirmek lazım.",
    "Akşam yemeği için çorba yapıyoruz. Annem yardım ediyor. Ev çok güzel kokuyor.",
    "Yağmur yağıyor. Şemsiyemi aldım. Sokakta yürüyorum. Su birikintilerine basmıyorum.",
    "Köpeğim çok sadık. Her gün onunla oynuyorum. Top getiriyor ve koşuyor.",
    "Saatin kaç? Şu an öğlen. Mide acıktı. Yemek yeme zamanı geldi.",
    "Çiçekler açtı. Bahar geldi. Ağaçlar yeşerdi. Doğa uyandı.",
    "Telefonum şarj oluyor. Ekran büyük. Ses yüksek. Kalitesi iyi.",
    "Kütüphaneye gittim. Çok kitap var. Sessiz ortam. Okumak için ideal.",
    "Spor yapmak sağlıklı. Koşmak iyi gelir. Ter atmak lazım. Su içmek önemli.",
    "Kardeşim okulda. Annem işte. Babam evde. Ben odamda ders çalışıyorum.",
    "Marketten ekmek aldım. Süt de aldım. Yumurta da lazım. Poşet ağır oldu.",
    "Televizyon seyrediyorum. Haberler geliyor. Hava durumu sonrasında film var.",
]

MEDIUM_TEXTS = [
    "Bilgisayar kullanırken klavyeye bakmadan yazmak büyük bir avantajdır. Bu beceriyi kazanmak için düzenli pratik yapmak gerekir. Her tuşa doğru parmakla basmak, hataları azaltır ve hızı artırır.",
    "Türkçe dilinin zenginliği, her geçen gün daha iyi anlaşılıyor. Kelimeler, cümleler ve anlatım biçimleri ile düşüncelerimizi ifade ederiz. On parmak yazma becerisi, bu ifadeyi hızlı ve doğru şekilde aktarmanın en iyi yoludur.",
    "Sabah erken kalkıp yeni güne hazırlanmak, verimli bir günün başlangıcıdır. Bir bardak su içmek, hafif bir kahvaltı yapmak ve kısa bir yürüyüş yapmak güne enerjik başlamanı sağlar.",
    "Teknoloji dünyası hızla değişiyor ve gelişiyor. Yapay zeka, bulut bilişim ve mobil teknolojiler hayatımızın ayrılmaz bir parçası haline geldi. Bu gelişmelere ayak uydurmak için sürekli öğrenmek gerekiyor.",
    "Doğa, bize her mevsim farklı güzellikler sunar. İlkbaharda çiçekler açar, yazın güneş parlar, sonbaharda yapraklar renk değiştirir, kışın ise beyaz örtü her yeri kaplar. Her mevsimin kendine özgü bir büyüsü vardır.",
    "On parmak yazma yöntemi, her bir parmağın klavye üzerinde belirli bir bölgeye atanmasıyla çalışır. Bu sayede yazarken klavyeye bakmaya gerek kalmaz ve yazma hızı önemli ölçüde artar.",
    "Türkiye'nin üç tarafı denizlerle çevrilidir. Karadeniz, Ege Denizi ve Akdeniz, ülkenin farklı bölgelerinde farklı iklim koşulları yaratır. Bu denizler aynı zamanda zengin balık çeşitliliği sunar.",
    "Eğitim, bir toplumun geleceğini şekillendiren en önemli unsurdur. İyi bir eğitim sistemi, bireylerin potansiyellerini ortaya çıkarmalarına olanak tanır ve toplumun genel refah seviyesini yükseltir.",
    "Sağlıklı yaşam için dengeli beslenme, düzenli spor ve yeterli uyku şarttır. Fast food tüketimini azaltmak, taze sebze ve meyve tüketimini artırmak vücudumuzun direncini güçlendirir.",
    "İnternet, bilgiye erişimi kolaylaştıran önemli bir araçtır. Ancak doğru bilgiyi ayırt edebilmek için eleştirel düşünme becerisine sahip olmak gerekir. Kaynak doğrulaması yapmak her zaman önemlidir.",
    "Müzik, insan ruhunu en derinden etkileyen sanat dallarından biridir. Farklı türlerdeki müzikler, farklı duyguları tetikler. Kimi zaman hüzün, kimi zaman neşe, kimi zaman ise huzur verir.",
    "Seyahat etmek, yeni kültürler tanımak ve farklı yaşam biçimleri görmek için harika bir yoldur. Her şehrin kendine özgü bir ruhu, bir kokusu ve bir rengi vardır. Yolculuk, insana kendini de tanıtır.",
    "Zaman yönetimi, modern yaşamın en önemli becerilerinden biridir. Öncelikleri belirlemek, gereksiz işleri elemek ve önemli konulara odaklanmak, hem iş hem de özel yaşamda başarıyı getirir.",
    "Çevre kirliliği, günümüzün en büyük sorunlarından biridir. Plastik atıklar, hava kirliliği ve su kirliliği doğayı tehdit ediyor. Her bireyin çevreyi korumak için bir şeyler yapması gerekiyor.",
    "Kitaplar, insan zihnini genişleten en değerli araçlardır. Romanlar hayal gücünü geliştirir, bilim kitapları bilgiyi derinleştirir, şiir kitapları ise duyguları besler. Okumak bir yaşam biçimidir.",
    "Sosyal medya, iletişim biçimimizi kökten değiştirdi. İnsanlar artık dünyanın diğer ucundaki kişilerle anında iletişim kurabiliyor. Ancak sosyal medyanın olumsuz etkilerine de dikkat etmek gerekir.",
    "Dil öğrenmek, beyin gelişimi için son derece faydalıdır. Yeni bir dil öğrenen kişilerin problem çözme becerileri artar, kültürel ufukları genişler ve iş fırsatları çoğalır.",
    "Tarih, geçmişten ders çıkarmamızı sağlayan önemli bir disiplindir. Geçmişte yaşanan olayları incelemek, bugünü anlamamıza ve geleceğe daha bilinçli adımlarla ilerlememize yardımcı olur.",
    "Bilim, evrenin işleyişini anlamamızı sağlayan sistematik bir yöntemdir. Gözlem, deney ve analitik düşünceyle çalışan bilim insanları, insanlığın yaşamını kökten değiştiren keşifler yapmıştır.",
    "Sanat, insanların duygularını ve düşüncelerini ifade etme biçimidir. Resim, heykel, tiyatro, sinema ve edebiyat gibi farklı sanat dalları, zengin ve çeşitli bir kültürel miras oluşturur.",
]

HARD_TEXTS = [
    "Teknoloji, günümüzde hayatın her alanına derinlemesine nüfuz etmiştir. Bilgisayarlar, akıllı telefonlar ve internet, iletişimi ve bilgiye erişimi kökten değiştirmiştir. Hızlı ve doğru yazma becerisi, bu dijital dünyada verimli olmanın temel anahtarlarından biridir. On parmak yazma tekniğini öğrenen bir kişi, hem zamandan tasarruf eder hem de daha az yorgunluk hisseder.",
    "Türk edebiyatının köklü geçmişi, binlerce yıllık bir birikimi barındırır. Divan edebiyatının incelikleri, halk edebiyatının samimiyeti ve modern Türk edebiyatının çok yönlülüğü, bu zengin mirasın farklı yüzleridir. Yahya Kemal, Tevfik Fikret, Orhan Pamuk ve Elif Şafak gibi yazarlar, Türkçe'nin gücünü dünya çapında göstermiştir.",
    "Kuantum fiziği, maddenin en küçük birimlerinin davranışlarını inceleyen modern fiziğin en önemli dallarından biridir. Atom altı parçacıkların hem dalga hem de parçacık özellikleri göstermesi, klasik fizik kurallarının yetersiz kaldığı bir alanı ortaya çıkarmıştır. Heisenberg belirsizlik ilkesi, bu dünyanın en temel kurallarından biridir.",
    "İklim değişikliği, günümüzde insanlığın karşı karşıya kaldığı en büyük küresel tehditlerden biridir. Fosil yakıtların kullanımı, ormanların yok edilmesi ve sanayileşmenin artmasıyla atmosferdeki karbondioksit miktarı hızla yükselmektedir. Bu durumun kutuplardaki buzulların erimesine, deniz seviyelerinin yükselmesine ve aşırı hava olaylarının artmasına neden olduğu bilimsel olarak kanıtlanmıştır.",
    "Felsefe, varoluşun, bilginin ve ahlakın temel sorularını sorgulayan disiplinlerarası bir alandır. Sokrates'in 'bilmediğini bilmesi'nden Kant'ın 'saf aklın eleştirisi'ne, Nietzsche'nin 'üstinsan' kavramından Sartre'ın 'varoluşçuluk' felsefesine kadar düşünce tarihi, insanın kendini ve evreni anlamlandırma çabasının izlerini taşır.",
    "Türkiye Cumhuriyeti, 29 Ekim 1923'te Mustafa Kemal Atatürk tarafından ilan edilmiştir. Kurtuluş Savaşı'nın zaferle sonuçlanmasının ardından, Osmanlı İmparatorluğu'nun yerine kurulan yeni devlet, laiklik, cumhuriyetçilik, halkçılık, devletçilik, milliyetçilik ve inkılapçılık ilkeleri üzerine inşa edilmiştir. Atatürk Devrimleri, toplumu modern çağın standartlarına taşımayı amaçlamıştır.",
    "Yapay zeka ve makine öğrenmesi, son yıllarda kaydedilen devasa ilerlemelerle birlikte birçok sektörde devrim niteliğinde değişimler yaratmaktadır. Derin öğrenme algoritmaları, doğal dil işleme, görüntü tanıma ve otonom araçlar gibi alanlarda insan seviyesinde performans gösterebilmektedir. Ancak bu gelişmeler, etik ve güvenlik konularında da önemli tartışmaları beraberinde getirmektedir.",
    "İnsan beyni, bilinen en karmaşık yapılardan biridir. Yaklaşık seksen altı milyar nöron hücresinden oluşan bu organ, her bir nöronun binlerce diğer nöronla bağlantı kurmasıyla inanılmaz bir bilgi işleme ağı oluşturur. Hafıza, öğrenme, duygusal tepkiler ve karar verme süreçlerinin tamamı bu kompleks ağ içinde gerçekleşir.",
    "Türk mutfağı, asırlar boyunca farklı medeniyetlerin etkileşimiyle zenginleşmiş, dünyanın en çeşitli mutfaklarından biridir. Kebap çeşitleri, çorba türleri, hamur işleri, zeytinyağlı yemekler ve tatlılar, bu zengin mutfağın sadece birkaç örnekleridir. Anadolu'nun her bölgesi, kendine özgü tarifleri ve pişirme teknikleriyle mutfak kültürüne katkıda bulunmuştur.",
    "Uzay keşfi, insanlığın en büyük maceralarından biridir. Ay'a ayak basılması, Mars'a gönderilen rover'lar, dış güneş sistemindeki uyduların incelenmesi ve ötegezegen keşifleri, evrenin gizemlerini çözme çabamızın önemli kilometre taşlarıdır. James Webb Uzay Teleskobu gibi gelişmiş araçlar, bu keşifleri daha da ileri taşıyacaktır.",
    "Ekonomi, toplumların sınırlı kaynaklarını nasıl tahsis ettiklerini inceleyen bir sosyal bilimdir. Mikroekonomi, bireysel tüketici ve firma davranışlarını incelerken; makroekonomi, ulusal gelir, enflasyon, işsizlik ve büyüme gibi toplam değişkenlerle ilgilenir. Adam Smith'in 'görünmez el' kavramından modern oyun teorisine kadar ekonomi düşünce tarihi büyük bir evrim geçirmiştir.",
    "Müzik teorisi, seslerin yükseklik, süre ve şiddet özelliklerini matematiksel ve estetik bir çerçevede inceler. Armoni, kontrpuan ve form analizleri, bir eserin yapısal özelliklerini anlamamızı sağlar. Barok, klasik, romantik ve modern dönemlerin her biri, müziğin ifade gücünü farklı şekillerde kullanmış ve zenginleştirmiştir.",
    "Türkçe, Ural-Altay dil ailesinin Altay koluna bağlı bir dildir ve dünyanın en çok konuşulan dilleri arasında yer alır. Agglutinatif yapısıyla kelime türetme konusunda son derece esnektir. Büyük ünlü uyumu ve küçük ünlü uyumu gibi seslik kurallar, dilin karakteristik özelliklerindendir. Türkçe'nin zengin kelime hazinesi, binlerce yıllık kültürel birikimin yansımasıdır.",
    "Biyoloji, canlı organizmaları ve yaşam süreçlerini inceleyen geniş kapsamlı bir bilim dalıdır. Hücre biyolojisi, genetik, evrim, ekoloji ve anatomi gibi alt dalların her biri, yaşamın farklı yönünü aydılatır. Darwin'in evrim teorisi, Watson ve Crick'in DNA'nın çift sarmal yapısını keşfetmesi ve modern genetik mühendisliği, biyolojik bilimlerin dönüm noktalarıdır.",
    "Mimarlık, hem sanat hem de mühendislik disiplinlerini birleştiren bir meslek alanıdır. Bir binanın estetik, işlevsel ve yapısal gereksinimleri aynı anda karşılaması gerekir. Mimar Sinan'ın camileri, Frank Lloyd Wright'ın organik mimarisi ve Zaha Hadid'in dekonstrüktivist tasarımları, mimarlığın sınırları zorlayan örnekleridir.",
    "Psikoloji, insan davranışını ve zihinsel süreçleri bilimsel yöntemlerle inceleyen bir alandır. Bilişsel psikoloji, sosyal psikoloji, klinik psikoloji ve gelişimsel psikoloji gibi alt dallar, insan psikolojisinin farklı boyutlarını ele alır. Freud'un psikanalitik kuramından modern bilişsel-davranışçı terapiye kadar alan büyük bir dönüşüm geçermiştir.",
    "Güneş sistemi, yaklaşık dört buçuk milyar yıl önce oluşmuş ve sekiz gezegen ile sayısız daha küçük gök cisiminden oluşmaktadır. Dünya, yaşam barındıran tek gezegen olarak bilinirken; Mars'ta geçmişte sıvı su var olduğuna dair kanıtlar bulunmuştur. Jüpiter ve Satürn gibi gaz devleri, sistemin dış bölgelerinde devasa kütleleriyle yer alır.",
    "Hukuk, toplumsal düzenin sağlanması ve bireylerin haklarının korunması için oluşturulan kurallar bütünüdür. Anayasa hukuku, medeni hukuk, ceza hukuku ve idare hukuku gibi alt dalların her biri, toplumsal yaşamın farklı yönlerini düzenler. Hukukun üstünlüğü ilkesi, demokratik toplumların temel taşlarından biridir.",
    "Edebiyat eleştirisi, bir metnin yapısal, tematik ve estetik özelliklerini sistematik biçimde değerlendiren disiplindir. Yeni eleştiri, yapısalçılık, postyapısalçılık ve feminist eleştiri gibi yaklaşımların her biri, metni farklı bir perspektiften okur. Bir eserin çok katmanlı anlamlarını ortaya çıkarmak, eleştirel okuma becerisi gerektirir.",
    "Tıp, insan sağlığını koruma, hastalıkları tedavi etme ve yaşam kalitesini iyileştirme amacı güden bir bilim ve sanat dalıdır. Anatomi, fizyoloji, farmakoloji ve patoloji gibi temel bilimler, klinik uygulamaların altyapısını oluşturur. Modern tıpta genetik tedaviler, immunoterapi ve robotik cerrahi gibi yenilikçi yaklaşımlar hızla yaygınlaşmaktadır.",
]

TEST_TEXTS = {
    "easy": EASY_TEXTS,
    "medium": MEDIUM_TEXTS,
    "hard": HARD_TEXTS,
}

ALL_TEXTS = EASY_TEXTS + MEDIUM_TEXTS + HARD_TEXTS

LEVEL_NAMES = {0: "easy", 1: "medium", 2: "hard"}


def get_texts(level: str = "medium") -> list:
    """Return the list of texts for the given difficulty level."""
    return TEST_TEXTS.get(level, MEDIUM_TEXTS)


def get_random_text(level: str = "medium") -> str:
    """Return a random text from the given difficulty level."""
    return random.choice(get_texts(level))
