"""Custom text page: import .txt, paste text, or pick presets to practice."""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QTextEdit, QFileDialog, QMessageBox,
)

from ...core.typing_engine import TypingEngine
from ...database.models import SessionRecord, MAX_TEXT_LENGTH
from ..widgets.typing_area import TypingArea
from ..widgets.finger_guide import FingerGuide
from ..widgets.results_dialog import ResultsDialog
from .base import BasePage, TypingPageMixin
from ..theme import palette

PRESETS = [
    ("🇹🇷 Türkiye", [
        "Türkiye, üç kıtanın kesiştiği stratejik bir konuma sahiptir.",
        "Anadolu yarımadası, binlerce yıllık medeniyetlere ev sahipliği yapmıştır.",
        "İstanbul, iki kıtayı birleştiren tek şehir olarak tarihte eşsizdir.",
        "Türkiye'nin en uzun nehri Kızılırmak'tır ve iç Anadolu'da akar.",
        "Kapadokya bölgesi, peri bacaları ve kayadan oyma evleriyle ünlüdür.",
        "Türk mutfağı, kebap çeşitleri ve zengin tatlılarıyla dünyada tanınır.",
        "Ankara, Türkiye'nin başkenti ve ikinci büyük şehridir.",
        "Türkiye, Karadeniz ve Akdeniz kıyılarıyla zengin bir doğaya sahiptir.",
        "Selçuklu ve Osmanlı devletleri, Anadolu'da derin izler bırakmıştır.",
        "Türkiye Cumhuriyeti, millet iradesine dayanan bir yönetim anlayışına sahiptir.",
    ]),
    ("📝 İstiklal", [
        "Korkma, sönmez bu şafaklarda yüzen alsancak.",
        "Sönmeden yurdumun üstünde tüten en son ocak.",
        "O benim milletimin yıldızıdır, parlayacak.",
        "O benindir, benim milletimindir.",
        "Çatma, kurban olayım, çehreni ey nazlı hilal.",
        "Kahraman ırkıma bir gülşen, ne bu şiddet, bu celal.",
        "Sana olmaz dökülen kanlarımız sonra helal.",
        "Hakkıdır, Hakk'a tapan, milletimin istiklal.",
        "İstiklal marşımız, milletimizin bağımsızlık ruhunu yansıtır.",
        "Bağımsızlık, bir milletin en kutsal ve vazgeçilmez değeridir.",
    ]),
    ("💡 Bilgelik", [
        "Bilgi, paylaştıkça çoğalan tek hazinedir.",
        "Öğrenmek yaşamdır, durmak değil.",
        "Okumak, insanın kendisiyle ve dünyayla buluşma yoludur.",
        "Sabırla öğrenilen her şey, hayat boyu unutulmaz.",
        "Bilgi güçtür, ancak kullanılırsa değer kazanır.",
        "Merak, bilimin ışığı ve keşfin motorudur.",
        "Hata yapmaktan korkmayanlar gerçekten öğrenir.",
        "Düşünmek, zihne açılan pencerenin en genişidir.",
        "Her yeni kelime, zihnine yeni bir dünya katar.",
        "Bilgelik, yılların deneyimi ve sabrının meyvesidir.",
    ]),
    ("📖 Dil", [
        "Türkçe, Ural-Altay dil ailesinin Altay koluna bağlı bir dildir.",
        "Agglutinatif yapısıyla kelime türetme konusunda son derece esnektir.",
        "Türkçe, sekiz ünlü ve yirmi bir ünsüz harften oluşur.",
        "Dil, bir milletin kimliği ve kültürel aynasıdır.",
        "Kelime dağarcığı zengin olanın, ifade gücü de güçlü olur.",
        "Türkçede büyük ünlü uyumu kuralı köklü kelimelerde görülür.",
        "Dil öğrenmek, yeni bir dünyaya açılan kapıyı aralamaktır.",
        "İyi bir diksiyon, etkili iletişimin temel taşıdır.",
        "Türkçe, binlerce yıllık tarihi geçmişe sahip zengin bir dildir.",
        "Kelimeleri doğru kullanmak, düşünceleri net ifade etmektir.",
    ]),
    ("🌍 Doğa", [
        "Doğa, bize her mevsim farklı güzellikler sunar.",
        "İlkbaharda çiçekler açar, yazın güneş parlar.",
        "Sonbaharda yapraklar renk değiştirir, kışın kar yağar.",
        "Ormanlar, dünyanın ciğerleri ve oksijen kaynağıdır.",
        "Su, yaşamın kaynağı ve en değerli kaynağımızdır.",
        "Hayvanları korumak, doğal dengeyi sağlamanın yoludur.",
        "Gerçek çevrecilik, doğaya zarar vermeden yaşamaktır.",
        "Dağlar, yeryüzünün görkemli ve güçlü heykelleridir.",
        "Denizler, dünyanın üçte ikisini kaplar ve yaşam barındırır.",
        "Her canlı, ekosistemin ayrılmaz bir parçasıdır.",
    ]),
    ("⚙️ Teknoloji", [
        "Bilgisayar kullanırken klavyeye bakmadan yazmak büyük bir avantajdır.",
        "Her tuşa doğru parmakla basmak, hataları azaltır ve hızı artırır.",
        "On parmak yazma tekniği, verimliliği önemli ölçüde yükseltir.",
        "Klavye kısayolları, zaman tasarrufu sağlayan kullanışlı araçlardır.",
        "Dijital çağda hızlı yazmak, rekabet gücünü artıran bir beceridir.",
        "Yazılım geliştirme, analitik düşünme ve sabır gerektiren bir iştir.",
        "İnternet, bilgiye erişimi kolaylaştıran güçlü bir araçtır.",
        "Teknoloji, doğru kullanıldığında hayatı kolaylaştırır.",
        "Programlama dilleri, bilgisayarla insan arasında köprü kurar.",
        "Verimli çalışmak, doğru araçlar ve iyi alışkanlıklar gerektirir.",
    ]),
]

EST_WPM = 40


class CustomTextPage(BasePage, TypingPageMixin):
    """Practice on custom text — paste, import .txt, or pick a preset."""

    def __init__(self, ctx, parent=None):
        super().__init__(ctx, parent)
        self.engine = TypingEngine(self.ctx.layout)
        self._active = False
        self._init_typing_mixin()
        self.add_header_with_stats(
            "Özel Metin", "Kendi metninle pratik yap — yaz, yapıştır veya hazır seç",
            self.ctx.show_timer, self.ctx.show_wpm,
        )
        self._build_ui()

    def _chip_style(self) -> str:
        p = palette(self.ctx.theme)
        return (
            f"QPushButton {{ border: 1px solid {p['border_input']}; border-radius: 16px; "
            f"padding: 6px 14px; font-size: 12px; font-weight: 600; "
            f"background: transparent; color: {p['text_secondary']}; }}"
            f"QPushButton:hover {{ background-color: {p['primary']}22; border-color: {p['primary']}; color: {p['text']}; }}"
        )

    def _build_ui(self) -> None:
        p = palette(self.ctx.theme)
        preset_card = QFrame()
        preset_card.setObjectName("card")
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(16, 12, 16, 12)
        preset_layout.setSpacing(8)

        preset_title = QLabel("⚡ Hızlı Seç")
        preset_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        preset_layout.addWidget(preset_title)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        chip_style = self._chip_style()
        for label, sentences in PRESETS:
            chip = QPushButton(label)
            chip.setStyleSheet(chip_style)
            chip.clicked.connect(lambda checked, s=sentences: self._load_preset(s))
            preset_row.addWidget(chip)
        preset_row.addStretch()
        preset_layout.addLayout(preset_row)
        self._root.addWidget(preset_card)

        input_card = QFrame()
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)

        input_header = QHBoxLayout()
        input_title = QLabel("✍️ Metin")
        input_title.setStyleSheet("font-size: 14px; font-weight: 600;")
        input_header.addWidget(input_title)
        input_header.addStretch()

        self._char_count_lbl = QLabel("0 karakter • 0 kelime")
        self._char_count_lbl.setStyleSheet(f"font-size: 12px; color: {p['text_muted']};")
        input_header.addWidget(self._char_count_lbl)
        input_layout.addLayout(input_header)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Metni buraya yapıştır, dosya yükle veya yukarıdan hazır seç...")
        self.text_edit.setFixedHeight(80)
        self.text_edit.textChanged.connect(self._update_counts)
        input_layout.addWidget(self.text_edit)

        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        import_btn = QPushButton("📁 Dosya Aç")
        import_btn.setObjectName("secondary")
        import_btn.clicked.connect(self._import_file)
        info_row.addWidget(import_btn)

        clear_btn = QPushButton("🗑️ Temizle")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._clear_text)
        info_row.addWidget(clear_btn)

        info_row.addStretch()

        self._est_time_lbl = QLabel("")
        self._est_time_lbl.setStyleSheet(f"font-size: 12px; color: {p['text_muted']};")
        info_row.addWidget(self._est_time_lbl)

        self.start_btn = QPushButton("▶ Pratiği Başlat")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self._start_practice)
        info_row.addWidget(self.start_btn)

        input_layout.addLayout(info_row)
        self._root.addWidget(input_card)

        self._warn_lbl = QLabel("")
        self._warn_lbl.setStyleSheet(f"color: {p['warning']}; font-size: 12px; padding: 2px 16px;")
        self._warn_lbl.setVisible(False)
        self._root.addWidget(self._warn_lbl)

        self.typing_area = TypingArea(self.engine, self.ctx.font_size, self.ctx.show_timer, self.ctx.theme)
        self._root.addWidget(self.typing_area)
        self.typing_area.finished.connect(self._on_finished)
        self.typing_area.statsUpdated.connect(self.update_header_stats)

        self.finger_guide = FingerGuide(self.ctx.layout)
        self._root.addWidget(self.finger_guide)

    def _load_preset(self, sentences: list) -> None:
        text = random.choice(sentences)
        self.text_edit.setPlainText(text)
        self._update_counts()

    def _clear_text(self) -> None:
        self.text_edit.clear()
        self._update_counts()

    def _update_counts(self) -> None:
        text = self.text_edit.toPlainText().strip()
        chars = len(text)
        words = len(text.split()) if text else 0
        self._char_count_lbl.setText(f"{chars} karakter • {words} kelime")
        if words > 0:
            est_secs = int(words / EST_WPM * 60)
            if est_secs < 60:
                self._est_time_lbl.setText(f"⏱️ ~{est_secs}s")
            else:
                self._est_time_lbl.setText(f"⏱️ ~{est_secs // 60}dk {est_secs % 60}s")
        else:
            self._est_time_lbl.setText("")

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Metin Dosyası Aç", "", "Metin Dosyaları (*.txt);;Tüm Dosyalar (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.text_edit.setPlainText(f.read())
                self._update_counts()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Dosya okunamadı: {e}")

    def _start_practice(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        if len(text) > MAX_TEXT_LENGTH:
            self._warn_lbl.setText(
                f"⚠️ Metin çok uzun ({len(text)} karakter). İlk {MAX_TEXT_LENGTH} karakter kullanılacak."
            )
            self._warn_lbl.setVisible(True)
            text = text[:MAX_TEXT_LENGTH]
        else:
            self._warn_lbl.setVisible(False)
        self._active = True
        self.typing_area.set_text(text)
        self._highlight_next_key()
        self.window().setFocus()

    def _is_active(self) -> bool:
        return self._active

    def _on_finished(self, result) -> None:
        self._active = False
        self.ctx.sound.play_success()
        self.finger_guide.clear()
        record = SessionRecord(
            mode="custom",
            mode_detail="custom_text",
            text_content=self.engine.target_text,
            total_chars=result.total_chars,
            correct_chars=result.correct_chars,
            incorrect_chars=result.incorrect_chars,
            wpm=result.wpm,
            raw_wpm=result.raw_wpm,
            accuracy=result.accuracy,
            max_wpm=result.max_wpm,
            key_counts=result.key_counts,
            started_at=result.started_at,
        )
        self._save_session(record)
        self._check_achievements()
        dialog = ResultsDialog(result, "Özel Metin Tamamlandı", self, show_retry=True)
        dialog.retry_requested.connect(self._start_practice)
        dialog.exec()

    def pause_page(self) -> None:
        self.typing_area.pause()

    def resume_page(self) -> None:
        self.typing_area.resume()
