"""
SISTEM AI SEDERHANA UNTUK MENDETEKSI PROKRASTINASI MAHASISWA
Author: AI Assistant
Deskripsi: Sistem ini menggunakan analisis pola perilaku, 
           manajemen waktu, dan kebiasaan belajar untuk mendeteksi
           kecenderungan prokrastinasi pada mahasiswa.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta, time
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import warnings

# Nonaktifkan semua warnings
warnings.filterwarnings("ignore")

# Set style untuk visualisasi
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


@dataclass
class AktivitasMahasiswa:
    """Data class untuk merepresentasikan aktivitas mahasiswa"""
    id_aktivitas: int
    jenis: str  # 'belajar', 'tugas', 'istirahat', 'hiburan', 'lainnya'
    deskripsi: str
    durasi: float  # dalam jam
    tanggal: str
    waktu_mulai: str
    deadline_terkait: Optional[str] = None
    tingkat_kesulitan: int = 1  # 1-10
    produktivitas: int = 3  # 1-10


@dataclass
class TugasMahasiswa:
    """Data class untuk merepresentasikan tugas mahasiswa"""
    id_tugas: int
    mata_kuliah: str
    deskripsi: str
    deadline: str
    tanggal_diberikan: str
    status: str  # 'belum', 'dikerjakan', 'selesai', 'terlambat'
    tanggal_selesai: Optional[str] = None
    tingkat_kesulitan: int = 3
    estimasi_waktu: float = 5.0
    waktu_aktual: Optional[float] = None


class SistemDeteksiProkrastinasi:
    """
    Sistem AI untuk mendeteksi prokrastinasi mahasiswa
    Menggunakan analisis pola aktivitas dan manajemen waktu
    """
    def __init__(self, nama_mahasiswa: str, nim: str) -> None:
        """Inisialisasi sistem deteksi prokrastinasi"""
        self.nama_mahasiswa = nama_mahasiswa
        self.nim = nim
        self.aktivitas: List[AktivitasMahasiswa] = []
        self.tugas: List[TugasMahasiswa] = []
        self.metrik_prokrastinasi: Dict[str, Any] = {}
    
    def tambah_aktivitas(self, aktivitas: AktivitasMahasiswa) -> None:
        """Menambahkan aktivitas baru ke dalam sistem"""
        self.aktivitas.append(aktivitas)
        print(f"Aktivitas '{aktivitas.deskripsi}' berhasil ditambahkan.")
    
    def tambah_tugas(self, tugas: TugasMahasiswa) -> None:
        """Menambahkan tugas baru ke dalam sistem"""
        self.tugas.append(tugas)
        print(f"Tugas '{tugas.deskripsi}' berhasil ditambahkan.")
    
    def analisis_pola_waktu(self) -> Dict[str, Any]:
        """
        Menganalisis pola penggunaan waktu mahasiswa
        Returns: Dictionary dengan hasil analisis
        """
        if not self.aktivitas:
            return {"error": "Tidak ada data aktivitas"}
        
        # Konversi ke DataFrame untuk analisis
        df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
        df_aktivitas['tanggal'] = pd.to_datetime(df_aktivitas['tanggal'])
        
        # Analisis distribusi waktu
        distribusi_waktu = df_aktivitas.groupby('jenis')['durasi'].sum()
        total_waktu = distribusi_waktu.sum()
        
        # Hitung persentase
        persentase_waktu = (distribusi_waktu / total_waktu * 100).round(2)
        
        # PERBAIKAN: Deteksi waktu produktif dengan cara yang benar
        def parse_waktu_mulai(waktu_str: str) -> time:
            """Parse string waktu ke objek time"""
            try:
                return datetime.strptime(waktu_str, '%H:%M').time()
            except (ValueError, TypeError):
                # Default ke 12:00 jika format salah
                return datetime.strptime('12:00', '%H:%M').time()
        
        # Gabungkan tanggal dan waktu
        def gabung_tanggal_waktu(row):
            """Gabungkan tanggal dan waktu_mulai"""
            tanggal = row['tanggal'].date()
            waktu_obj = parse_waktu_mulai(str(row['waktu_mulai']))
            return datetime.combine(tanggal, waktu_obj)
        
        # Tambahkan kolom datetime lengkap
        df_aktivitas['datetime_mulai'] = df_aktivitas.apply(gabung_tanggal_waktu, axis=1)
        df_aktivitas['jam'] = df_aktivitas['datetime_mulai'].dt.hour
        
        # Kategorikan jam
        def kategorikan_jam(jam: int) -> str:
            """Mengkategorikan jam menjadi periode hari"""
            if 5 <= jam < 12:
                return 'Pagi'
            elif 12 <= jam < 17:
                return 'Siang'
            elif 17 <= jam < 22:
                return 'Sore/Malam'
            else:
                return 'Tengah Malam'
        
        df_aktivitas['periode_hari'] = df_aktivitas['jam'].apply(kategorikan_jam)
        
        # Hitung waktu produktif
        if not df_aktivitas.empty:
            waktu_produktif = df_aktivitas.groupby('periode_hari')['produktivitas'].mean()
            rata_produktivitas = float(df_aktivitas['produktivitas'].mean())
        else:
            waktu_produktif = pd.Series(dtype=float)
            rata_produktivitas = 0.0
        
        return {
            'distribusi_waktu': distribusi_waktu.to_dict(),
            'persentase_waktu': persentase_waktu.to_dict(),
            'total_waktu_tercatat': float(total_waktu),
            'waktu_produktif': waktu_produktif.to_dict(),
            'rata_rata_produktivitas': rata_produktivitas
        }
    
    def hitung_indeks_prokrastinasi(self) -> Dict[str, Any]:
        """
        Menghitung indeks prokrastinasi berdasarkan multiple faktor
        Returns: Dictionary dengan skor dan interpretasi
        """
        if not self.tugas:
            return {"error": "Tidak ada data tugas"}
        
        df_tugas = pd.DataFrame([asdict(t) for t in self.tugas])
        df_tugas['deadline'] = pd.to_datetime(df_tugas['deadline'])
        df_tugas['tanggal_diberikan'] = pd.to_datetime(df_tugas['tanggal_diberikan'])
        
        # Inisialisasi skor
        skor_total = 0
        faktor_penilaian: Dict[str, Any] = {}
        
        # 1. Faktor Keterlambatan
        tugas_terlambat = df_tugas[df_tugas['status'] == 'terlambat'].shape[0]
        total_tugas = df_tugas.shape[0]
        persentase_terlambat = (tugas_terlambat / total_tugas * 100) if total_tugas > 0 else 0
        
        if persentase_terlambat > 30:
            skor_keterlambatan = 3
        elif persentase_terlambat > 15:
            skor_keterlambatan = 2
        elif persentase_terlambat > 0:
            skor_keterlambatan = 1
        else:
            skor_keterlambatan = 0
        
        faktor_penilaian['keterlambatan'] = {
            'skor': skor_keterlambatan,
            'persentase_terlambat': round(float(persentase_terlambat), 2),
            'jumlah_tugas_terlambat': int(tugas_terlambat),
            'total_tugas': int(total_tugas)
        }
        skor_total += skor_keterlambatan
        
        # 2. Faktor Jarak Mulai Pengerjaan
        if 'tanggal_selesai' in df_tugas.columns and df_tugas['tanggal_selesai'].notna().any():
            # Konversi ke datetime jika belum
            df_tugas['tanggal_selesai'] = pd.to_datetime(df_tugas['tanggal_selesai'])
            
            # Hitung waktu pengerjaan
            mask_selesai = df_tugas['tanggal_selesai'].notna()
            if mask_selesai.any():
                df_tugas_selesai = df_tugas[mask_selesai].copy()
                df_tugas_selesai['waktu_pengerjaan'] = (
                    df_tugas_selesai['tanggal_selesai'] - df_tugas_selesai['tanggal_diberikan']
                ).dt.days
                
                rata_waktu_pengerjaan = float(df_tugas_selesai['waktu_pengerjaan'].mean())
                
                if rata_waktu_pengerjaan > 14:
                    skor_waktu = 3
                elif rata_waktu_pengerjaan > 7:
                    skor_waktu = 2
                elif rata_waktu_pengerjaan > 3:
                    skor_waktu = 1
                else:
                    skor_waktu = 0
                
                faktor_penilaian['waktu_pengerjaan'] = {
                    'skor': skor_waktu,
                    'rata_rata_hari': round(rata_waktu_pengerjaan, 2),
                    'jumlah_tugas_selesai': int(mask_selesai.sum())
                }
                skor_total += skor_waktu
        
        # 3. Faktor Rasio Hiburan vs Belajar
        if self.aktivitas:
            df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
            
            # Filter dan hitung waktu
            waktu_belajar = float(df_aktivitas[df_aktivitas['jenis'] == 'belajar']['durasi'].sum())
            waktu_tugas = float(df_aktivitas[df_aktivitas['jenis'] == 'tugas']['durasi'].sum())
            waktu_hiburan = float(df_aktivitas[df_aktivitas['jenis'] == 'hiburan']['durasi'].sum())
            total_waktu = float(df_aktivitas['durasi'].sum())
            
            if total_waktu > 0:
                waktu_produktif = waktu_belajar + waktu_tugas
                rasio_hiburan = (waktu_hiburan / total_waktu * 100) if total_waktu > 0 else 0
                rasio_produktif = (waktu_produktif / total_waktu * 100) if total_waktu > 0 else 0
                
                if rasio_hiburan > 40:
                    skor_rasio = 3
                elif rasio_hiburan > 25:
                    skor_rasio = 2
                elif rasio_hiburan > 15:
                    skor_rasio = 1
                else:
                    skor_rasio = 0
                
                faktor_penilaian['rasio_hiburan'] = {
                    'skor': skor_rasio,
                    'persentase_hiburan': round(float(rasio_hiburan), 2),
                    'persentase_produktif': round(float(rasio_produktif), 2),
                    'waktu_hiburan': round(waktu_hiburan, 2),
                    'waktu_produktif': round(waktu_produktif, 2)
                }
                skor_total += skor_rasio
        
        # 4. Faktor Konsistensi
        if self.aktivitas:
            df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
            df_aktivitas['tanggal'] = pd.to_datetime(df_aktivitas['tanggal'])
            
            # Hitung aktivitas harian
            aktivitas_harian = df_aktivitas.groupby('tanggal').size()
            
            if len(aktivitas_harian) > 1:  # Minimal 2 hari untuk hitung std
                deviasi_konsistensi = float(aktivitas_harian.std())
                
                if deviasi_konsistensi > 3:
                    skor_konsistensi = 2
                elif deviasi_konsistensi > 1.5:
                    skor_konsistensi = 1
                else:
                    skor_konsistensi = 0
                
                faktor_penilaian['konsistensi'] = {
                    'skor': skor_konsistensi,
                    'deviasi_aktivitas': round(deviasi_konsistensi, 2),
                    'rata_aktivitas_harian': round(float(aktivitas_harian.mean()), 2),
                    'jumlah_hari': len(aktivitas_harian)
                }
                skor_total += skor_konsistensi
        
        # Hitung maksimum skor yang mungkin
        # Faktor yang dinilai: keterlambatan(3), waktu_pengerjaan(3), rasio_hiburan(3), konsistensi(2) = total 11
        maksimum_skor = 11
        
        # Normalisasi skor (0-10)
        if skor_total > 0:
            skor_normalized = (skor_total / maksimum_skor) * 10
        else:
            skor_normalized = 0.0
        
        # Batasi maksimal 10
        skor_normalized = min(10.0, skor_normalized)
        
        # **PERBAIKAN UTAMA: Logika interpretasi yang lebih akurat**
        if skor_normalized >= 8.0:  # 80% atau lebih
            tingkat_prokrastinasi = "TINGGI"
            rekomendasi = "⚠️ PERLU INTERVENSI SERIUS! Tingkat prokrastinasi sangat tinggi. Segera konsultasi dengan pembimbing akademik dan pertimbangkan bantuan profesional."
        elif skor_normalized >= 6.0:  # 60-79%
            tingkat_prokrastinasi = "SEDANG-TINGGI"
            rekomendasi = "⏰ PERLU PERBAIKAN SEGERA! Manajemen waktu tidak optimal. Buat jadwal harian yang ketat, gunakan teknik Pomodoro, dan tetapkan deadline internal."
        elif skor_normalized >= 4.0:  # 40-59%
            tingkat_prokrastinasi = "SEDANG"
            rekomendasi = "📝 PERLU PERBAIKAN. Ada beberapa pola prokrastinasi. Mulai dengan membuat prioritas tugas dan kurangi waktu hiburan selama periode sibuk."
        elif skor_normalized >= 2.0:  # 20-39%
            tingkat_prokrastinasi = "RENDAH-SEDANG"
            rekomendasi = "✅ CUKUP BAIK. Pertahankan kebiasaan baik. Fokus pada konsistensi dan coba selesaikan tugas lebih awal dari deadline."
        else:  # 0-19%
            tingkat_prokrastinasi = "RENDAH"
            rekomendasi = "🎉 SANGAT BAIK! Tingkat prokrastinasi rendah. Pertahankan kebiasaan produktif dan disiplin yang sudah ada."
        
        self.metrik_prokrastinasi = {
            'skor_total': round(skor_normalized, 2),
            'skor_mentah': skor_total,
            'maksimum_skor': maksimum_skor,
            'tingkat': tingkat_prokrastinasi,
            'faktor_penilaian': faktor_penilaian,
            'rekomendasi': rekomendasi
        }
        
        return self.metrik_prokrastinasi
    
    def prediksi_risiko_tugas(self, deadline: str, tingkat_kesulitan: int) -> Dict[str, Any]:
        """
        Memprediksi risiko prokrastinasi untuk tugas baru
        berdasarkan riwayat perilaku
        """
        if not self.metrik_prokrastinasi:
            self.hitung_indeks_prokrastinasi()
        
        try:
            deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
            hari_ini = datetime.now()
            hari_tersisa = (deadline_dt - hari_ini).days
            
            # Pastikan hari_tersisa tidak negatif
            if hari_tersisa < 0:
                hari_tersisa = 0
        except ValueError:
            return {"error": "Format deadline tidak valid. Gunakan format YYYY-MM-DD"}
        
        # Faktor prediksi
        faktor_skor = self.metrik_prokrastinasi.get('skor_total', 5.0)
        faktor_kesulitan = tingkat_kesulitan / 10.0  # Normalisasi 0-1 (karena skala 1-10)
        
        # Hitung risiko
        risiko_dasar = (faktor_skor / 10 * 0.6) + (faktor_kesulitan * 0.4)
        
        # Adjust berdasarkan waktu tersisa
        if hari_tersisa < 3:
            risiko_penyesuaian = min(1.0, risiko_dasar * 1.5)
        elif hari_tersisa < 7:
            risiko_penyesuaian = min(1.0, risiko_dasar * 1.2)
        else:
            risiko_penyesuaian = min(1.0, risiko_dasar)
        
        # Kategorikan risiko
        if risiko_penyesuaian > 0.7:
            kategori_risiko = "SANGAT TINGGI"
            tindakan = "Segera mulai kerjakan hari ini! Buat rencana harian."
        elif risiko_penyesuaian > 0.5:
            kategori_risiko = "TINGGI"
            tindakan = "Buat deadline internal lebih awal dari deadline sebenarnya."
        elif risiko_penyesuaian > 0.3:
            kategori_risiko = "SEDANG"
            tindakan = "Breakdown tugas menjadi subtask kecil."
        else:
            kategori_risiko = "RENDAH"
            tindakan = "Pertahankan konsistensi pengerjaan."
        
        return {
            'deadline': deadline,
            'hari_tersisa': hari_tersisa,
            'tingkat_kesulitan': tingkat_kesulitan,
            'skor_risiko': round(float(risiko_penyesuaian * 10), 2),
            'kategori_risiko': kategori_risiko,
            'tindakan_rekomendasi': tindakan,
            'prediksi_selesai': self._prediksi_tanggal_selesai(hari_tersisa, float(risiko_penyesuaian))
        }
    
    def _prediksi_tanggal_selesai(self, hari_tersisa: int, risiko: float) -> str:
        """Memprediksi tanggal selesai berdasarkan risiko prokrastinasi"""
        hari_ini = datetime.now()
        
        # Pastikan hari_tersisa positif
        if hari_tersisa <= 0:
            return hari_ini.strftime('%Y-%m-%d')
        
        if risiko > 0.7:
            # High risk: akan menyelesaikan mendekati deadline
            hari_prediksi = max(1, int(hari_tersisa * 0.2))
        elif risiko > 0.5:
            hari_prediksi = max(1, int(hari_tersisa * 0.4))
        elif risiko > 0.3:
            hari_prediksi = max(1, int(hari_tersisa * 0.6))
        else:
            # Low risk: akan menyelesaikan lebih awal
            hari_prediksi = max(1, int(hari_tersisa * 0.8))
        
        tanggal_prediksi = hari_ini + timedelta(days=hari_prediksi)
        return tanggal_prediksi.strftime('%Y-%m-%d')
    
    def visualisasi_analisis(self) -> None:
        """Menghasilkan visualisasi analisis prokrastinasi yang lebih jelas"""
        if not self.aktivitas and not self.tugas:
            print("⚠️ Tidak ada data untuk divisualisasikan.")
            print("Silakan tambah data aktivitas dan tugas terlebih dahulu.")
            return
        
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle(f'ANALISIS PROKRASTINASI - {self.nama_mahasiswa.upper()} ({self.nim})', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Layout grid yang lebih terstruktur
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Distribusi Waktu Aktivitas (Pie Chart)
        ax1 = fig.add_subplot(gs[0, 0])
        if self.aktivitas:
            try:
                df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
                distribusi = df_aktivitas.groupby('jenis')['durasi'].sum()
                
                # Filter hanya jenis yang ada datanya
                distribusi = distribusi[distribusi > 0]
                
                if len(distribusi) > 0:
                    colors = plt.cm.Set3(np.linspace(0, 1, len(distribusi)))
                    wedges, texts, autotexts = ax1.pie(
                        distribusi.values, 
                        labels=distribusi.index, 
                        autopct='%1.1f%%',
                        colors=colors,
                        startangle=90,
                        wedgeprops=dict(width=0.6, edgecolor='w'),
                        textprops={'fontsize': 9}
                    )
                    
                    # Perbaiki teks autopct
                    for autotext in autotexts:
                        autotext.set_color('black')
                        autotext.set_fontweight('bold')
                    
                    ax1.set_title('Distribusi Waktu Aktivitas', fontsize=12, fontweight='bold', pad=15)
                    
                    # Tambahkan legenda
                    ax1.legend(
                        wedges, 
                        [f"{label}: {distribusi[label]:.1f} jam" for label in distribusi.index],
                        title="Jenis Aktivitas",
                        loc="center left",
                        bbox_to_anchor=(1, 0, 0.5, 1),
                        fontsize=9
                    )
                else:
                    ax1.text(0.5, 0.5, 'Tidak ada data aktivitas\natau semua durasi = 0', 
                            ha='center', va='center', fontsize=10)
                    ax1.set_title('Distribusi Waktu Aktivitas', fontsize=12)
            except Exception as e:
                ax1.text(0.5, 0.5, f'Error: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax1.set_title('Distribusi Waktu Aktivitas', fontsize=12)
        else:
            ax1.text(0.5, 0.5, 'Belum ada data aktivitas', 
                    ha='center', va='center', fontsize=10)
            ax1.set_title('Distribusi Waktu Aktivitas', fontsize=12)
        
        # 2. Trend Produktivitas Harian
        ax2 = fig.add_subplot(gs[0, 1:])
        if self.aktivitas:
            try:
                df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
                df_aktivitas['tanggal'] = pd.to_datetime(df_aktivitas['tanggal'])
                
                # Kelompokkan berdasarkan tanggal dan hitung rata-rata produktivitas
                produktivitas_harian = df_aktivitas.groupby('tanggal')['produktivitas'].mean()
                
                if len(produktivitas_harian) > 0:
                    # Plot garis trend
                    ax2.plot(produktivitas_harian.index, produktivitas_harian.values, 
                            marker='o', linewidth=2, markersize=6, color='royalblue', 
                            markerfacecolor='white', markeredgecolor='royalblue', markeredgewidth=2)
                    
                    # Garis threshold (skala 1-10, threshold di 5)
                    ax2.axhline(y=5, color='red', linestyle='--', alpha=0.7, linewidth=1.5, 
                              label='Threshold Normal (5.0)')
                    
                    # Fill area
                    ax2.fill_between(produktivitas_harian.index, 
                                   produktivitas_harian.values, 
                                   5, where=(produktivitas_harian.values >= 5),
                                   alpha=0.3, color='green', label='Produktif')
                    ax2.fill_between(produktivitas_harian.index, 
                                   produktivitas_harian.values, 
                                   5, where=(produktivitas_harian.values < 5),
                                   alpha=0.3, color='orange', label='Kurang Produktif')
                    
                    # Format tanggal
                    ax2.set_title('Trend Produktivitas Harian', fontsize=12, fontweight='bold', pad=10)
                    ax2.set_xlabel('Tanggal', fontsize=10)
                    ax2.set_ylabel('Rata-rata Produktivitas (Skala 1-10)', fontsize=10)
                    ax2.legend(loc='upper right', fontsize=9)
                    ax2.grid(True, alpha=0.3)
                    
                    # Rotasi label tanggal
                    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha='right')
                    
                    # Set y-limits
                    ax2.set_ylim([0.5, 10.5])
                    
                    # Anotasi titik tertinggi dan terendah
                    if len(produktivitas_harian) > 1:
                        max_idx = produktivitas_harian.idxmax()
                        min_idx = produktivitas_harian.idxmin()
                        ax2.annotate(f'Highest: {produktivitas_harian[max_idx]:.1f}', 
                                   xy=(max_idx, produktivitas_harian[max_idx]),
                                   xytext=(10, 10), textcoords='offset points',
                                   fontsize=8, color='darkgreen',
                                   arrowprops=dict(arrowstyle='->', color='darkgreen', alpha=0.7))
                        ax2.annotate(f'Lowest: {produktivitas_harian[min_idx]:.1f}', 
                                   xy=(min_idx, produktivitas_harian[min_idx]),
                                   xytext=(10, -10), textcoords='offset points',
                                   fontsize=8, color='darkred',
                                   arrowprops=dict(arrowstyle='->', color='darkred', alpha=0.7))
                else:
                    ax2.text(0.5, 0.5, 'Tidak ada data produktivitas', 
                            ha='center', va='center', fontsize=10)
                    ax2.set_title('Trend Produktivitas Harian', fontsize=12)
            except Exception as e:
                ax2.text(0.5, 0.5, f'Error: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax2.set_title('Trend Produktivitas Harian', fontsize=12)
        else:
            ax2.text(0.5, 0.5, 'Belum ada data aktivitas', 
                    ha='center', va='center', fontsize=10)
            ax2.set_title('Trend Produktivitas Harian', fontsize=12)
        
        # 3. Status Tugas (Bar Chart)
        ax3 = fig.add_subplot(gs[1, 0])
        if self.tugas:
            try:
                df_tugas = pd.DataFrame([asdict(t) for t in self.tugas])
                status_counts = df_tugas['status'].value_counts()
                
                # Mapping warna untuk status
                status_colors = {
                    'selesai': 'green',
                    'dikerjakan': 'orange',
                    'belum': 'red',
                    'terlambat': 'darkred'
                }
                
                colors = [status_colors.get(status, 'gray') for status in status_counts.index]
                
                if len(status_counts) > 0:
                    bars = ax3.bar(status_counts.index, status_counts.values, color=colors, edgecolor='black')
                    ax3.set_title('Distribusi Status Tugas', fontsize=12, fontweight='bold', pad=10)
                    ax3.set_xlabel('Status', fontsize=10)
                    ax3.set_ylabel('Jumlah Tugas', fontsize=10)
                    ax3.grid(True, alpha=0.3, axis='y')
                    
                    # Tambahkan nilai di atas bar
                    for bar in bars:
                        height = bar.get_height()
                        ax3.text(bar.get_x() + bar.get_width()/2., float(height) + 0.1,
                               f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                    
                    # Rotasi label x jika perlu
                    ax3.tick_params(axis='x', rotation=30)
                    
                    # Tambahkan total tugas
                    ax3.text(0.02, 0.98, f'Total: {len(df_tugas)} tugas', 
                            transform=ax3.transAxes, fontsize=9, va='top')
                else:
                    ax3.text(0.5, 0.5, 'Tidak ada data tugas', 
                            ha='center', va='center', fontsize=10)
                    ax3.set_title('Distribusi Status Tugas', fontsize=12)
            except Exception as e:
                ax3.text(0.5, 0.5, f'Error: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax3.set_title('Distribusi Status Tugas', fontsize=12)
        else:
            ax3.text(0.5, 0.5, 'Belum ada data tugas', 
                    ha='center', va='center', fontsize=10)
            ax3.set_title('Distribusi Status Tugas', fontsize=12)
        
        # 4. Aktivitas per Periode Hari (Bar Chart Horizontal)
        ax4 = fig.add_subplot(gs[1, 1])
        if self.aktivitas:
            try:
                df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
                
                # Parse waktu mulai
                def parse_waktu_mulai(waktu_str: str) -> time:
                    try:
                        return datetime.strptime(waktu_str, '%H:%M').time()
                    except (ValueError, TypeError):
                        return datetime.strptime('12:00', '%H:%M').time()
                
                df_aktivitas['datetime_mulai'] = df_aktivitas.apply(
                    lambda row: datetime.combine(
                        pd.to_datetime(row['tanggal']).date(), 
                        parse_waktu_mulai(str(row['waktu_mulai']))
                    ), axis=1
                )
                df_aktivitas['jam'] = df_aktivitas['datetime_mulai'].dt.hour
                
                # Kategorikan jam
                def kategorikan_jam(jam: int) -> str:
                    if 5 <= jam < 12:
                        return 'Pagi (05:00-11:59)'
                    elif 12 <= jam < 17:
                        return 'Siang (12:00-16:59)'
                    elif 17 <= jam < 22:
                        return 'Sore/Malam (17:00-21:59)'
                    else:
                        return 'Tengah Malam (22:00-04:59)'
                
                df_aktivitas['periode_hari'] = df_aktivitas['jam'].apply(kategorikan_jam)
                
                # Hitung durasi per periode
                durasi_periode = df_aktivitas.groupby('periode_hari')['durasi'].sum()
                
                if len(durasi_periode) > 0:
                    # Urutkan periode
                    periode_order = ['Pagi (05:00-11:59)', 'Siang (12:00-16:59)', 
                                   'Sore/Malam (17:00-21:59)', 'Tengah Malam (22:00-04:59)']
                    durasi_periode = durasi_periode.reindex(periode_order, fill_value=0)
                    
                    colors_periode = ['#FFD700', '#FFA500', '#4169E1', '#4B0082']
                    bars = ax4.barh(list(durasi_periode.index), durasi_periode.values, 
                                  color=colors_periode, edgecolor='black')
                    ax4.set_title('Aktivitas per Periode Hari', fontsize=12, fontweight='bold', pad=10)
                    ax4.set_xlabel('Total Durasi (Jam)', fontsize=10)
                    ax4.grid(True, alpha=0.3, axis='x')
                    
                    # Tambahkan nilai di ujung bar
                    for bar in bars:
                        width = bar.get_width()
                        ax4.text(width + 0.1, bar.get_y() + bar.get_height()/2., 
                               f'{width:.1f} jam', ha='left', va='center', fontsize=9)
                else:
                    ax4.text(0.5, 0.5, 'Tidak ada data periode', 
                            ha='center', va='center', fontsize=10)
                    ax4.set_title('Aktivitas per Periode Hari', fontsize=12)
            except Exception as e:
                ax4.text(0.5, 0.5, f'Error: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax4.set_title('Aktivitas per Periode Hari', fontsize=12)
        else:
            ax4.text(0.5, 0.5, 'Belum ada data aktivitas', 
                    ha='center', va='center', fontsize=10)
            ax4.set_title('Aktivitas per Periode Hari', fontsize=12)
        
        # 5. Tingkat Kesulitan vs Produktivitas (Scatter Plot)
        ax5 = fig.add_subplot(gs[1, 2])
        if self.aktivitas:
            try:
                df_aktivitas = pd.DataFrame([asdict(a) for a in self.aktivitas])
                
                if len(df_aktivitas) > 0:
                    scatter = ax5.scatter(
                        df_aktivitas['tingkat_kesulitan'], 
                        df_aktivitas['produktivitas'],
                        c=df_aktivitas['durasi'], 
                        s=df_aktivitas['durasi'] * 50,  # Ukuran berdasarkan durasi
                        alpha=0.7,
                        cmap='viridis',
                        edgecolor='black',
                        linewidth=0.5
                    )
                    
                    # Colorbar
                    cbar = plt.colorbar(scatter, ax=ax5)
                    cbar.set_label('Durasi (Jam)', fontsize=9)
                    
                    ax5.set_title('Tingkat Kesulitan vs Produktivitas', fontsize=12, fontweight='bold', pad=10)
                    ax5.set_xlabel('Tingkat Kesulitan (1-10)', fontsize=10)
                    ax5.set_ylabel('Produktivitas (1-10)', fontsize=10)
                    ax5.set_xlim([0.5, 10.5])
                    ax5.set_ylim([0.5, 10.5])
                    ax5.grid(True, alpha=0.3)
                    
                    # Garis rata-rata
                    mean_kesulitan = df_aktivitas['tingkat_kesulitan'].mean()
                    mean_produktivitas = df_aktivitas['produktivitas'].mean()
                    ax5.axhline(y=mean_produktivitas, color='red', linestyle='--', 
                              alpha=0.5, linewidth=1, label=f'Avg Produktif: {mean_produktivitas:.1f}')
                    ax5.axvline(x=mean_kesulitan, color='blue', linestyle='--', 
                              alpha=0.5, linewidth=1, label=f'Avg Kesulitan: {mean_kesulitan:.1f}')
                    ax5.legend(fontsize=8)
                else:
                    ax5.text(0.5, 0.5, 'Tidak ada data untuk scatter plot', 
                            ha='center', va='center', fontsize=10)
                    ax5.set_title('Tingkat Kesulitan vs Produktivitas', fontsize=12)
            except Exception as e:
                ax5.text(0.5, 0.5, f'Error: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax5.set_title('Tingkat Kesulitan vs Produktivitas', fontsize=12)
        else:
            ax5.text(0.5, 0.5, 'Belum ada data aktivitas', 
                    ha='center', va='center', fontsize=10)
            ax5.set_title('Tingkat Kesulitan vs Produktivitas', fontsize=12)
        
        # 6. Indeks Prokrastinasi (Gauge Chart yang lebih baik)
        ax6 = fig.add_subplot(gs[2, :])
        if self.metrik_prokrastinasi and 'skor_total' in self.metrik_prokrastinasi:
            try:
                skor = float(self.metrik_prokrastinasi['skor_total'])
                tingkat = self.metrik_prokrastinasi['tingkat']
                
                # Buat gauge chart yang lebih sederhana dan jelas
                ax6 = plt.subplot(gs[2, :])
                
                # Buat gauge background (semi-circle)
                theta = np.linspace(0, np.pi, 100)
                r = np.ones_like(theta)
                
                # Zona warna
                ax6.fill_between(theta, 0, r, where=(theta <= np.pi/3), 
                               alpha=0.3, color='green', label='RENDAH (0-3.3)')
                ax6.fill_between(theta, 0, r, where=(theta > np.pi/3) & (theta <= 2*np.pi/3), 
                               alpha=0.3, color='orange', label='SEDANG (3.4-6.6)')
                ax6.fill_between(theta, 0, r, where=(theta > 2*np.pi/3), 
                               alpha=0.3, color='red', label='TINGGI (6.7-10)')
                
                # Garis indikator skor
                skor_angle = (skor / 10) * np.pi
                ax6.plot([0, skor_angle], [0, 0.8], color='black', linewidth=3, label=f'Skor: {skor}/10')
                ax6.plot(0, 0, 'ko', markersize=10)  # Titik pusat
                
                # Text pada gauge
                ax6.text(skor_angle/2, 0.4, f'{skor:.1f}/10', 
                        ha='center', va='center', fontsize=14, fontweight='bold')
                
                # Anotasi zona
                ax6.text(np.pi/6, 1.05, 'RENDAH', ha='center', va='center', fontsize=10)
                ax6.text(np.pi/2, 1.05, 'SEDANG', ha='center', va='center', fontsize=10)
                ax6.text(5*np.pi/6, 1.05, 'TINGGI', ha='center', va='center', fontsize=10)
                
                # Title dan detail
                ax6.set_title(f'INDEKS PROKRASTINASI - {tingkat}', fontsize=14, fontweight='bold', pad=20)
                ax6.text(0.5, -0.3, 
                        f"Skor: {skor:.2f}/10 | Status: {tingkat} | Rekomendasi: {self.metrik_prokrastinasi.get('rekomendasi', 'N/A')[:60]}...", 
                        ha='center', va='center', transform=ax6.transAxes, fontsize=10)
                
                ax6.set_xlim([-0.1, np.pi + 0.1])
                ax6.set_ylim([-0.1, 1.1])
                ax6.set_aspect('equal')
                ax6.axis('off')
                
            except Exception as e:
                ax6.text(0.5, 0.5, f'Error gauge chart: {str(e)[:30]}...', 
                        ha='center', va='center', fontsize=10, color='red')
                ax6.set_title('Indeks Prokrastinasi', fontsize=12)
                ax6.axis('off')
        else:
            ax6.text(0.5, 0.5, 'Belum ada indeks prokrastinasi\nKlik Menu 4 untuk menghitung', 
                    ha='center', va='center', fontsize=11)
            ax6.set_title('Indeks Prokrastinasi', fontsize=12)
            ax6.axis('off')
        
        # Atur layout
        plt.tight_layout()
        
        # Simpan gambar
        try:
            filename = f"analisis_prokrastinasi_{self.nim}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            print(f"\n✅ Visualisasi berhasil disimpan sebagai '{filename}'")
        except Exception as e:
            print(f"⚠️ Error menyimpan visualisasi: {e}")
        
        plt.show()
    
    def generate_report(self) -> str:
        """Generate laporan analisis prokrastinasi"""
        if not self.metrik_prokrastinasi:
            self.hitung_indeks_prokrastinasi()
        
        report = f"""
{'='*60}
LAPORAN ANALISIS PROKRASTINASI MAHASISWA
{'='*60}

MAHASISWA:
Nama    : {self.nama_mahasiswa}
NIM     : {self.nim}
Tanggal : {datetime.now().strftime('%d/%m/%Y %H:%M')}

{'='*60}
HASIL ANALISIS:
{'='*60}

Indeks Prokrastinasi: {self.metrik_prokrastinasi.get('skor_total', 'N/A')}/10
Tingkat Prokrastinasi: {self.metrik_prokrastinasi.get('tingkat', 'N/A')}

FAKTOR PENILAIAN:
"""
        
        faktor_penilaian = self.metrik_prokrastinasi.get('faktor_penilaian', {})
        if faktor_penilaian:
            for faktor, detail in faktor_penilaian.items():
                report += f"\n{faktor.upper()}:\n"
                for key, value in detail.items():
                    report += f"  {key}: {value}\n"
        else:
            report += "\nBelum ada faktor penilaian yang dihitung.\n"
        
        report += f"""
{'='*60}
REKOMENDASI:
{'='*60}

{self.metrik_prokrastinasi.get('rekomendasi', 'Belum ada rekomendasi')}

STATISTIK AKTIVITAS:
Total Aktivitas Tercatat: {len(self.aktivitas)}
Total Tugas: {len(self.tugas)}

"""
        
        if self.aktivitas:
            analisis_waktu = self.analisis_pola_waktu()
            if 'persentase_waktu' in analisis_waktu and analisis_waktu['persentase_waktu']:
                report += "DISTRIBUSI WAKTU:\n"
                for jenis, persen in analisis_waktu['persentase_waktu'].items():
                    report += f"  {jenis}: {persen}%\n"
        
        report += f"\n{'='*60}"
        report += "\nSARAN TINDAK LANJUT:\n"
        report += "1. Gunakan teknik Pomodoro (25 menit fokus, 5 menit istirahat)\n"
        report += "2. Buat to-do list harian dengan prioritas yang jelas\n"
        report += "3. Tetapkan deadline internal 2-3 hari sebelum deadline sebenarnya\n"
        report += "4. Kurangi distraksi (matikan notifikasi, gunakan website blocker)\n"
        report += "5. Lacak progres harian untuk meningkatkan akuntabilitas\n"
        report += f"{'='*60}"
        
        # Simpan laporan ke file
        filename = f"laporan_prokrastinasi_{self.nim}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Laporan berhasil disimpan sebagai '{filename}'")
        except Exception as e:
            print(f"Error menyimpan laporan: {e}")
        
        return report
    
    def simpan_data(self, filename: str = "data_prokrastinasi.json") -> None:
        """Menyimpan data ke file JSON"""
        try:
            data = {
                'mahasiswa': {
                    'nama': self.nama_mahasiswa,
                    'nim': self.nim
                },
                'aktivitas': [asdict(a) for a in self.aktivitas],
                'tugas': [asdict(t) for t in self.tugas],
                'metrik_prokrastinasi': self.metrik_prokrastinasi,
                'tanggal_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Data berhasil disimpan ke '{filename}'")
        except Exception as e:
            print(f"Error menyimpan data: {e}")
    
    def muat_data(self, filename: str = "data_prokrastinasi.json") -> None:
        """Memuat data dari file JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.nama_mahasiswa = data['mahasiswa']['nama']
                self.nim = data['mahasiswa']['nim']
                
                # Load aktivitas
                self.aktivitas = []
                for aktivitas_data in data.get('aktivitas', []):
                    try:
                        aktivitas = AktivitasMahasiswa(**aktivitas_data)
                        self.aktivitas.append(aktivitas)
                    except Exception as e:
                        print(f"Error loading aktivitas: {e}")
                
                # Load tugas
                self.tugas = []
                for tugas_data in data.get('tugas', []):
                    try:
                        tugas = TugasMahasiswa(**tugas_data)
                        self.tugas.append(tugas)
                    except Exception as e:
                        print(f"Error loading tugas: {e}")
                
                self.metrik_prokrastinasi = data.get('metrik_prokrastinasi', {})
                
                print(f"Data berhasil dimuat dari '{filename}'")
                print(f"  - Aktivitas: {len(self.aktivitas)} entri")
                print(f"  - Tugas: {len(self.tugas)} entri")
            else:
                print(f"File '{filename}' tidak ditemukan.")
        except Exception as e:
            print(f"Error memuat data: {e}")

    def generate_data_dummy(self) -> None:
        """Generate data dummy untuk testing visualisasi"""
        from datetime import datetime, timedelta
        
        # Reset data
        self.aktivitas = []
        self.tugas = []
        
        # Generate tanggal
        start_date = datetime.now() - timedelta(days=14)
        
        # Data aktivitas dummy
        jenis_list = ['belajar', 'tugas', 'istirahat', 'hiburan', 'lainnya']
        waktu_mulai_list = ['08:00', '10:00', '13:00', '15:00', '19:00', '21:00']
        
        for i in range(30):
            tanggal = (start_date + timedelta(days=i%7)).strftime('%Y-%m-%d')
            jenis = jenis_list[i % len(jenis_list)]
            durasi = np.random.uniform(0.5, 3.0)
            produktivitas = np.random.randint(2, 9)  # Skala 1-10
            tingkat_kesulitan = np.random.randint(1, 8) if jenis in ['belajar', 'tugas'] else 1
            
            aktivitas = AktivitasMahasiswa(
                id_aktivitas=i+1,
                jenis=jenis,
                deskripsi=f"Aktivitas {jenis} {i+1}",
                durasi=round(durasi, 1),
                tanggal=tanggal,
                waktu_mulai=waktu_mulai_list[i % len(waktu_mulai_list)],
                tingkat_kesulitan=tingkat_kesulitan,
                produktivitas=produktivitas
            )
            self.aktivitas.append(aktivitas)
        
        # Data tugas dummy
        mata_kuliah_list = ['Matematika', 'Fisika', 'Kimia', 'Biologi', 'Sejarah']
        
        for i in range(10):
            deadline_date = datetime.now() + timedelta(days=np.random.randint(1, 30))
            given_date = deadline_date - timedelta(days=np.random.randint(5, 15))
            
            status_options = ['selesai', 'dikerjakan', 'belum', 'terlambat']
            weights = [0.3, 0.3, 0.3, 0.1]  # 10% kemungkinan terlambat untuk testing
            status = np.random.choice(status_options, p=weights)
            
            if status == 'selesai':
                selesai_date = given_date + timedelta(days=np.random.randint(1, 5))
                tanggal_selesai = selesai_date.strftime('%Y-%m-%d')
                waktu_aktual = np.random.uniform(2, 8)
            else:
                tanggal_selesai = None
                waktu_aktual = None
            
            tugas = TugasMahasiswa(
                id_tugas=i+1,
                mata_kuliah=mata_kuliah_list[i % len(mata_kuliah_list)],
                deskripsi=f"Tugas {i+1} {mata_kuliah_list[i % len(mata_kuliah_list)]}",
                deadline=deadline_date.strftime('%Y-%m-%d'),
                tanggal_diberikan=given_date.strftime('%Y-%m-%d'),
                status=status,
                tanggal_selesai=tanggal_selesai,
                tingkat_kesulitan=np.random.randint(2, 9),  # Skala 1-10
                estimasi_waktu=np.random.uniform(3, 10),
                waktu_aktual=round(waktu_aktual, 1) if waktu_aktual else None
            )
            self.tugas.append(tugas)
        
        print("✅ Data dummy berhasil di-generate!")
        print(f"   - {len(self.aktivitas)} aktivitas")
        print(f"   - {len(self.tugas)} tugas")


def main() -> None:
    """Fungsi utama program"""
    print("="*70)
    print("SISTEM AI DETEKSI PROKRASTINASI MAHASISWA")
    print("="*70)
    
    # Inisialisasi sistem
    nama = input("Masukkan nama mahasiswa: ").strip()
    nim = input("Masukkan NIM: ").strip()
    
    sistem = SistemDeteksiProkrastinasi(nama, nim)
    
    print("\n" + "-"*50)
    print("APAKAH INGIN MEMUAT DATA SEBELUMNYA?")
    print("-"*50)
    muat_data = input("Muat data dari file? (y/n): ").strip().lower()
    
    if muat_data == 'y':
        filename = input("Nama file (default: data_prokrastinasi.json): ").strip()
        if not filename:
            filename = "data_prokrastinasi.json"
        
        # Simpan nama dan NIM yang baru diinput
        nama_asli = nama
        nim_asli = nim
        
        # Muat data dari file
        sistem.muat_data(filename)
        
        # Tanya apakah ingin menggunakan nama baru atau nama dari file
        print(f"\n✓ Data dimuat! Data berisi: {sistem.nama_mahasiswa} ({sistem.nim})")
        ganti_nama = input(f"Tetap gunakan nama '{nama_asli}'? (y/n): ").strip().lower()
        
        if ganti_nama == 'y':
            sistem.nama_mahasiswa = nama_asli
            sistem.nim = nim_asli
            print(f"✓ Nama diubah menjadi: {sistem.nama_mahasiswa}")
        else:
            print(f"✓ Menggunakan nama dari file: {sistem.nama_mahasiswa}")
    else:
        print(f"\n✓ Membuat data baru untuk {nama} ({nim})")
    
    print(f"\n" + "="*70)
    print(f"SELAMAT DATANG, {sistem.nama_mahasiswa.upper()}!")
    print(f"NIM: {sistem.nim}")
    print("="*70)
    
    while True:
        print("\n" + "="*70)
        print("MENU UTAMA")
        print("="*70)
        print("1. Tambah Aktivitas Harian")
        print("2. Tambah Tugas/Kewajiban")
        print("3. Analisis Pola Waktu")
        print("4. Hitung Indeks Prokrastinasi")
        print("5. Prediksi Risiko Prokrastinasi untuk Tugas Baru")
        print("6. Tampilkan Visualisasi Analisis")
        print("7. Generate Laporan Lengkap")
        print("8. Simpan Data")
        print("9. Muat Data")
        print("10. Generate Data Dummy untuk Testing")
        print("0. Keluar")
        print("="*70)
        
        pilihan = input("Pilih menu (0-10): ").strip()
        
        if pilihan == "1":
            print("\n" + "="*70)
            print("TAMBAH AKTIVITAS HARIAN")
            print("="*70)
            try:
                jenis = input("Jenis aktivitas (belajar/tugas/istirahat/hiburan/lainnya): ").strip().lower()
                deskripsi = input("Deskripsi aktivitas: ").strip()
                durasi = float(input("Durasi (jam): ").strip())
                tanggal = input("Tanggal (YYYY-MM-DD): ").strip()
                waktu_mulai = input("Waktu mulai (HH:MM): ").strip()
                tingkat_kesulitan = int(input("Tingkat kesulitan (1-10): ").strip())
                produktivitas = int(input("Tingkat produktivitas (1-10): ").strip())
                
                # Validasi input
                if tingkat_kesulitan < 1 or tingkat_kesulitan > 10:
                    print("❌ Tingkat kesulitan harus antara 1-10")
                    continue
                if produktivitas < 1 or produktivitas > 10:
                    print("❌ Tingkat produktivitas harus antara 1-10")
                    continue
                
                aktivitas = AktivitasMahasiswa(
                    id_aktivitas=len(sistem.aktivitas) + 1,
                    jenis=jenis,
                    deskripsi=deskripsi,
                    durasi=durasi,
                    tanggal=tanggal,
                    waktu_mulai=waktu_mulai,
                    tingkat_kesulitan=tingkat_kesulitan,
                    produktivitas=produktivitas
                )
                
                sistem.tambah_aktivitas(aktivitas)
                
            except ValueError as e:
                print(f"❌ Error: Input tidak valid - {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif pilihan == "2":
            print("\n" + "="*70)
            print("TAMBAH TUGAS")
            print("="*70)
            try:
                mata_kuliah = input("Mata kuliah: ").strip()
                deskripsi = input("Deskripsi tugas: ").strip()
                deadline = input("Deadline (YYYY-MM-DD): ").strip()
                tanggal_diberikan = input("Tanggal diberikan (YYYY-MM-DD): ").strip()
                status = input("Status (belum/dikerjakan/selesai/terlambat): ").strip().lower()
                
                # Validasi status
                if status not in ['belum', 'dikerjakan', 'selesai', 'terlambat']:
                    print("❌ Status harus: belum, dikerjakan, selesai, atau terlambat")
                    continue
                
                tingkat_kesulitan = int(input("Tingkat kesulitan (1-10): ").strip())
                estimasi_waktu = float(input("Estimasi waktu pengerjaan (jam): ").strip())
                
                # Validasi input
                if tingkat_kesulitan < 1 or tingkat_kesulitan > 10:
                    print("❌ Tingkat kesulitan harus antara 1-10")
                    continue
                
                if status == "selesai":
                    tanggal_selesai = input("Tanggal selesai (YYYY-MM-DD): ").strip()
                    waktu_aktual = float(input("Waktu aktual pengerjaan (jam): ").strip())
                else:
                    tanggal_selesai = None
                    waktu_aktual = None
                
                tugas = TugasMahasiswa(
                    id_tugas=len(sistem.tugas) + 1,
                    mata_kuliah=mata_kuliah,
                    deskripsi=deskripsi,
                    deadline=deadline,
                    tanggal_diberikan=tanggal_diberikan,
                    status=status,
                    tanggal_selesai=tanggal_selesai,
                    tingkat_kesulitan=tingkat_kesulitan,
                    estimasi_waktu=estimasi_waktu,
                    waktu_aktual=waktu_aktual
                )
                
                sistem.tambah_tugas(tugas)
                
            except ValueError as e:
                print(f"❌ Error: Input tidak valid - {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif pilihan == "3":
            print("\n" + "="*70)
            print("ANALISIS POLA WAKTU")
            print("="*70)
            hasil = sistem.analisis_pola_waktu()
            
            if 'error' in hasil:
                print(f"❌ {hasil['error']}")
                print("Silakan tambah aktivitas terlebih dahulu (Menu 1)")
            else:
                print("\n📊 DISTRIBUSI WAKTU:")
                for jenis, durasi in hasil['distribusi_waktu'].items():
                    print(f"  {jenis}: {durasi} jam ({hasil['persentase_waktu'][jenis]}%)")
                
                print(f"\n⏰ TOTAL WAKTU TERCATAT: {hasil['total_waktu_tercatat']} jam")
                
                if hasil['waktu_produktif']:
                    print(f"\n🌞 WAKTU PALING PRODUKTIF:")
                    for periode, produktivitas in hasil['waktu_produktif'].items():
                        print(f"  {periode}: {produktivitas:.2f}/10")
                else:
                    print("\n⚠️  Data waktu produktif tidak tersedia")
                
                print(f"\n📈 RATA-RATA PRODUKTIVITAS: {hasil['rata_rata_produktivitas']:.2f}/10")
        
        elif pilihan == "4":
            print("\n" + "="*70)
            print("INDEKS PROKRASTINASI".center(70))
            print("="*70)
            
            hasil = sistem.hitung_indeks_prokrastinasi()
            
            if 'error' in hasil:
                print(f"❌ {hasil['error']}")
                print("Silakan tambah tugas terlebih dahulu (Menu 2)")
            else:
                print(f"\n{'📊'*20}")
                print(f"🎯 SKOR PROKRASTINASI: {hasil['skor_total']}/10")
                print(f"📈 TINGKAT: {hasil['tingkat']}")
                print(f"{'📊'*20}")
                
                print(f"\n💡 REKOMENDASI:\n{hasil['rekomendasi']}")
                
                print(f"\n{'🔍'*20}")
                print("DETAIL FAKTOR PENILAIAN:")
                print(f"{'🔍'*20}")
                
                for faktor, detail in hasil['faktor_penilaian'].items():
                    print(f"\n📌 {faktor.upper().replace('_', ' ')}:")
                    for key, value in detail.items():
                        # Format key menjadi lebih readable
                        key_formatted = key.replace('_', ' ').title()
                        print(f"   • {key_formatted}: {value}")
                
                # Tampilkan kesimpulan
                print(f"\n{'✅'*20}")
                print("KESIMPULAN:")
                print(f"{'✅'*20}")
                print(f"Skor Akhir: {hasil['skor_total']}/10 ({hasil['tingkat']})")
        
        elif pilihan == "5":
            print("\n" + "="*70)
            print("PREDIKSI RISIKO PROKRASTINASI")
            print("="*70)
            try:
                deadline = input("Deadline tugas (YYYY-MM-DD): ").strip()
                tingkat_kesulitan = int(input("Tingkat kesulitan (1-10): ").strip())
                
                if tingkat_kesulitan < 1 or tingkat_kesulitan > 10:
                    print("❌ Tingkat kesulitan harus antara 1-10")
                    continue
                
                prediksi = sistem.prediksi_risiko_tugas(deadline, tingkat_kesulitan)
                
                if 'error' in prediksi:
                    print(f"❌ Error: {prediksi['error']}")
                else:
                    print(f"\n📋 HASIL PREDIKSI UNTUK TUGAS:")
                    print(f"   📅 Deadline: {prediksi['deadline']}")
                    print(f"   ⏳ Hari tersisa: {prediksi['hari_tersisa']} hari")
                    print(f"   🎯 Tingkat kesulitan: {prediksi['tingkat_kesulitan']}/10")
                    print(f"   ⚠️  Skor Risiko: {prediksi['skor_risiko']}/10")
                    print(f"   🚨 Kategori Risiko: {prediksi['kategori_risiko']}")
                    print(f"   📈 Prediksi Selesai: {prediksi['prediksi_selesai']}")
                    print(f"\n   ✅ TINDAKAN REKOMENDASI: {prediksi['tindakan_rekomendasi']}")
            except ValueError as e:
                print(f"❌ Error: Input tidak valid - {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        elif pilihan == "6":
            print("\n" + "="*70)
            print("VISUALISASI ANALISIS")
            print("="*70)
            sistem.visualisasi_analisis()
        
        elif pilihan == "7":
            print("\n" + "="*70)
            print("LAPORAN LENGKAP")
            print("="*70)
            laporan = sistem.generate_report()
            print(laporan)
        
        elif pilihan == "8":
            print("\n" + "="*70)
            print("SIMPAN DATA")
            print("="*70)
            filename = input("Nama file (default: data_prokrastinasi.json): ").strip()
            if not filename:
                filename = "data_prokrastinasi.json"
            sistem.simpan_data(filename)
        
        elif pilihan == "9":
            print("\n" + "="*70)
            print("MUAT DATA")
            print("="*70)
            filename = input("Nama file (default: data_prokrastinasi.json): ").strip()
            if not filename:
                filename = "data_prokrastinasi.json"
            sistem.muat_data(filename)
        
        elif pilihan == "10":
            print("\n" + "="*70)
            print("GENERATE DATA DUMMY UNTUK TESTING")
            print("="*70)
            konfirmasi = input("⚠️ Ini akan menghapus data yang ada. Lanjutkan? (y/n): ").strip().lower()
            if konfirmasi == 'y':
                sistem.generate_data_dummy()
                print("✅ Data dummy siap digunakan!")
            else:
                print("❌ Dibatalkan.")
        
        elif pilihan == "0":
            print("\n" + "="*70)
            print("KELUAR DARI PROGRAM")
            print("="*70)
            print("Keluar dari program...")
            try:
                sistem.simpan_data()  # Auto-save sebelum keluar
                print("✅ Data otomatis disimpan ke 'data_prokrastinasi.json'")
            except:
                print("⚠️  Gagal menyimpan data otomatis")
            print("Terima kasih telah menggunakan Sistem Deteksi Prokrastinasi!")
            break
        
        else:
            print("❌ Pilihan tidak valid. Silakan coba lagi.")


if __name__ == "__main__":
    try:
        print("Semua dependensi terpenuhi. Memulai program...\n")
        main()
    except ImportError as e:
        print(f"Error: Modul yang diperlukan tidak ditemukan: {e}")
        print("Silakan install dependensi dengan perintah:")
        print("pip install pandas matplotlib seaborn numpy")
    except Exception as e:
        print(f"Error tidak terduga: {e}")