# BUKU PANDUAN LEGAL CLM

## Panduan Pengguna Contract Lifecycle Management

Organisasi: PT Perfect Companion Indonesia  
Sistem: Legal CLM  
Jenis Dokumen: Buku Panduan Pengguna Akhir  
Versi: 2.2  
Tanggal Berlaku: 12 Mei 2026

---

## Persetujuan Dan Kendali Dokumen

| Field | Value |
|---|---|
| Pemilik dokumen | Legal Operations |
| Disusun oleh | CLM Project Team |
| Disetujui oleh | Head of Legal |
| Siklus tinjauan | Setiap 6 bulan |
| Distribusi | Hanya pengguna internal |

### Riwayat Revisi

| Versi | Tanggal | Ringkasan Perubahan | Penulis |
|---|---|---|---|
| 1.0 | 12 Mei 2026 | Manual pengguna awal | CLM Project Team |
| 2.0 | 12 Mei 2026 | Format buku panduan lengkap, struktur SOP, lampiran | CLM Project Team |
| 2.1 | 12 Mei 2026 | Menambahkan placeholder visual inline pada bagian terkait | CLM Project Team |
| 2.2 | 13 Mei 2026 | Menambahkan panduan alur sistem dan administrasi | CLM Project Team |

---

## Daftar Isi

1. Tujuan Dan Ruang Lingkup
2. Audiens Dan Peran
3. Persyaratan Akses Sistem
4. Peta Antarmuka Pengguna
5. Alur Utama
6. Standard Operating Procedures (SOP)
7. Panduan Siklus Hidup Kontrak
8. Tanggung Jawab Berdasarkan Peran
9. Standar Layanan Dan Kontrol
10. Panduan Troubleshooting
11. Pertanyaan Yang Sering Diajukan
12. Glosarium
13. Dukungan Dan Eskalasi
14. Panduan Ekspor PDF
15. Lampiran A: Kartu Quick Start
16. Lampiran B: Checklist Pra-Pengajuan
17. Lampiran C: Indeks Screenshot Yang Disarankan

---

## 1. Tujuan Dan Ruang Lingkup

Buku panduan ini adalah referensi resmi pengguna untuk Legal CLM. Dokumen ini menjelaskan cara pengguna membuat, meninjau, mengelola, dan memantau kontrak dari tahap draft hingga tahap aktif dan kedaluwarsa.

Panduan ini mencakup:
- login dan navigasi harian
- pembuatan kontrak dan input data
- pengelolaan participant, dokumen, komentar, dan tanda tangan
- manajemen status dan pengingat
- perilaku dan kontrol berbasis peran
- penanganan error umum dan alur dukungan

Panduan ini tidak mencakup:
- langkah deployment server
- perubahan source code
- administrasi infrastruktur di luar aplikasi

---

## 2. Audiens Dan Peran

Buku panduan ini dirancang untuk:
- Contract Owner: membuat dan mengelola kontrak
- Legal Reviewer: meninjau konten legal dan transisi status
- Business User: mengajukan data bisnis dan dokumen
- Signatory: menandatangani kontrak saat diminta
- Staff/Admin User: mengonfigurasi master data sistem dan permission

Jika peran Anda tidak jelas, hubungi administrator sebelum melakukan tindakan apa pun pada kontrak.

---

## 3. Persyaratan Akses Sistem

Sebelum menggunakan Legal CLM, pastikan:
- Anda memiliki username dan password yang valid
- akun pengguna Anda aktif
- browser Anda sudah versi terbaru
- file kontrak yang diperlukan tersedia
- Anda memiliki izin untuk mengakses kontrak terkait

Aturan keamanan:
- jangan pernah membagikan password Anda
- selalu logout setelah selesai
- hindari menggunakan perangkat bersama tanpa logout

---

## 4. Peta Antarmuka Pengguna

### Menu Navigasi Utama

Setelah login, sidebar kiri berisi:
- Dashboard
- All Contracts
- Create Contract
- Expiring Soon
- Terminated
- Admin Panel (khusus staff/admin)
- Logout

### Layar Utama

- Dashboard: ringkasan KPI dan tindakan utama
- All Contracts: registri kontrak yang dapat dicari
- Contract Detail: catatan kontrak lengkap beserta aksi
- Contract Wizard: panduan pembuatan kontrak 4 langkah
- Expiring Soon: pemantauan proaktif kontrak mendekati kedaluwarsa
- Admin Panel: kontrol pengaturan dan tata kelola

![Dashboard Overview](manual-images/img-02-dashboard.png)

![Admin Panel Overview](manual-images/img-13-admin-panel.png)

---

## 5. Alur Utama

Gunakan bagian ini saat Anda ingin memahami sistem sebagai sebuah proses, bukan hanya sebagai layar-layar terpisah.

### 5.1 Alur Sistem

Alur normal pengguna adalah:

Login -> Dashboard -> All Contracts atau Create Contract -> Contract Detail -> Participants / Documents / Comments / Status -> pemantauan Expiring Soon -> Logout

Cara menggunakan alur:
- mulai dari Dashboard setelah login
- gunakan All Contracts saat Anda perlu mencari data yang sudah ada
- gunakan Create Contract saat Anda memulai perjanjian baru
- gunakan Contract Detail untuk edit, komentar, participant, dan dokumen
- gunakan Expiring Soon untuk tindak lanjut perpanjangan dan penutupan

### 5.2 Alur Administrasi

Alur normal administrasi adalah:

Login sebagai Staff/Admin -> Buka Admin Panel -> Tinjau master data -> Konfigurasi jenis kontrak / field / template / permission / pengaturan email -> Simpan perubahan -> Uji dengan alur pengguna normal -> Logout

Cara menggunakan alur:
- lakukan perubahan hanya jika Anda berwenang
- ubah satu kelompok konfigurasi dalam satu waktu
- validasi hasil dengan membuat atau meninjau sampel kontrak
- pastikan pengguna tetap bisa login dan menjalankan alur kerja yang diharapkan

### 5.3 Alur Pembuatan Kontrak

Create Contract -> Pilih jenis entitas -> Unggah dokumen administratif -> Isi informasi kontrak -> Isi data terstruktur -> Simpan -> Tinjau draft -> Ajukan untuk legal review

Titik kontrol utama:
- jenis entitas menentukan field dan dokumen yang wajib
- file yang kurang atau nilai yang tidak valid akan menghentikan proses
- kontrak hanya boleh lanjut jika semua item wajib sudah lengkap

### 5.4 Alur Review Dan Revisi

Buka Contract Detail -> Baca dokumen dan komentar -> Tambahkan komentar legal atau bisnis -> Minta revisi jika diperlukan -> Unggah dokumen revisi -> Cek ulang -> Setujui atau perbarui status

Titik kontrol utama:
- komentar harus jelas menyebutkan apa yang harus diperbaiki
- revisi harus sesuai dengan isu yang diminta
- persetujuan akhir hanya dilakukan setelah perbaikan terverifikasi

---

## 6. Standard Operating Procedures (SOP)

## SOP 01 - Login Dan Logout

Tujuan: Mengakses sistem dengan aman.

Cara alur ini berjalan:
- Anda melakukan autentikasi terlebih dahulu
- sistem mengarahkan Anda ke Dashboard
- Anda mengakhiri sesi dengan logout

### Langkah

1. Buka URL Legal CLM.
2. Masukkan username dan password.
3. Klik Login.
4. Pastikan Dashboard muncul.
5. Di akhir sesi, klik Logout.

![Login Screen](manual-images/img-01-login.png)

### Kriteria Keberhasilan

- pengguna berhasil masuk ke Dashboard setelah login
- sesi pengguna berakhir setelah logout

### Error Umum

- kredensial tidak valid
- pengguna tidak aktif

### Tindakan Korektif

- masukkan ulang kredensial dengan teliti
- hubungi admin untuk aktivasi akun

---

## SOP 02 - Cari Kontrak

Tujuan: Menemukan kontrak yang benar dengan cepat.

Cara alur ini berjalan:
- mulai dari All Contracts
- persempit daftar menggunakan filter atau pencarian
- buka data yang benar sebelum melakukan perubahan

### Langkah

1. Buka All Contracts.
2. Gunakan filter: type, status, owner, start date, end date.
3. Gunakan keyword search untuk judul atau pihak.
4. Buka kontrak dengan klik judulnya.

![All Contracts List](manual-images/img-03-contract-list.png)

### Kriteria Keberhasilan

- halaman detail kontrak yang benar berhasil terbuka

### Titik Kontrol

- verifikasi nomor kontrak dan pihak sebelum edit

---

## SOP 03 - Buat Kontrak (Wizard 4 Langkah)

Tujuan: Membuat data kontrak yang valid dan paket awal.

Cara alur ini berjalan:
- langkah 1 memilih jenis entitas legal
- langkah 2 mengumpulkan dokumen pendukung
- langkah 3 mencatat informasi header kontrak
- langkah 4 menyimpan data template terstruktur
- sistem kemudian membuat data draft kontrak

### Langkah 1: Jenis Entitas Bisnis

1. Klik Create Contract.
2. Pilih jenis entitas legal mitra.
3. Klik Continue.

Catatan kontrol: pilihan ini mengatur dokumen dan field yang wajib.

![Wizard Step 1](manual-images/img-04-wizard-step-1.png)

### Langkah 2: Dokumen Administratif

1. Unggah dokumen administratif yang diwajibkan.
2. Pastikan setiap file terpasang pada field yang benar.
3. Klik Continue.

Catatan kualitas file:
- gunakan file yang jelas terbaca
- gunakan format file yang diizinkan di layar

![Wizard Step 2](manual-images/img-05-wizard-step-2.png)

### Langkah 3: Informasi Kontrak

1. Lengkapi data inti kontrak:
- title
- contract type
- informasi pihak
- tanggal
- nilai
- deskripsi
2. Tinjau pesan validasi field.
3. Klik Continue.

Catatan tanggal:
- beberapa template menghitung otomatis end date dari start date dan durasi

![Wizard Step 3](manual-images/img-06-wizard-step-3.png)

### Langkah 4: Data Terstruktur

1. Isi field khusus template.
2. Tinjau field yang wajib.
3. Klik Save Data atau Finish and Create Contract.

![Wizard Step 4](manual-images/img-07-wizard-step-4.png)

### Kriteria Keberhasilan

- kontrak berhasil dibuat
- data berhasil disimpan
- pembuatan draft terjadi saat template berlaku

---

## SOP 04 - Kelola Aksi Detail Kontrak

Tujuan: Menjalankan aksi pasca-pembuatan kontrak secara aman.

Cara alur ini berjalan:
- buka halaman detail kontrak
- tinjau status dan permission saat ini
- pilih aksi yang Anda butuhkan
- simpan dan pastikan perubahan tercatat di riwayat kontrak

### Aksi yang tersedia (bergantung peran)

- edit contract
- add participants
- upload documents
- add comments
- update status
- open structured data page
- upload final approved document

![Contract Detail Page](manual-images/img-08-contract-detail.png)

### Titik Kontrol

Sebelum melakukan aksi apa pun, verifikasi:
- nomor kontrak
- status saat ini
- kepemilikan dan permission

---

## SOP 05 - Tambah Participant

Tujuan: Menambahkan pengguna yang relevan ke alur kerja kontrak.

Cara alur ini berjalan:
- pengaturan participant dilakukan dari Contract Detail
- setiap participant mendapat peran dalam alur kerja
- peran menentukan apa yang bisa dilakukan berikutnya

### Langkah

1. Buka Contract Detail.
2. Klik Add Participant (jika terlihat).
3. Pilih pengguna dan peran.
4. Simpan.

![Participants Section](manual-images/img-09-participant-section.png)

### Kriteria Keberhasilan

- participant muncul di daftar participant

### Kontrol Risiko

- hindari memberi peran yang salah
- pastikan email/akun participant benar

---

## SOP 06 - Pengelolaan Dokumen Dan Tanda Tangan

Tujuan: Menjaga jejak dokumen tetap lengkap dan dapat diaudit.

Cara alur ini berjalan:
- unggah file kerja atau file pendukung terlebih dahulu
- minta atau kumpulkan tanda tangan saat diperlukan
- simpan versi final yang disetujui dengan identifikasi yang jelas

### Aksi dokumen

- upload source/supporting documents
- upload revised documents when requested
- upload final approved document

![Document Upload Section](manual-images/img-10-document-upload.png)

### Aksi tanda tangan

- signatory membuka permintaan tanda tangan
- menandatangani kontrak secara digital
- sistem menyimpan metadata penanda tangan, timestamp, dan IP

### Titik Kontrol

- pastikan file yang diunggah adalah versi final sebelum unggah final

---

## SOP 07 - Pengelolaan Komentar Dan Revisi

Tujuan: Memastikan seluruh komunikasi review tercatat.

Cara alur ini berjalan:
- tambahkan komentar review pada data kontrak
- minta perbaikan dengan instruksi yang jelas
- unggah file revisi setelah perbaikan
- cek ulang sebelum persetujuan

### Langkah

1. Buka Contract Detail.
2. Tambahkan komentar dengan instruksi yang jelas.
3. Jika revisi diminta, sebutkan bagian atau isu secara spesifik.
4. Unggah dokumen revisi saat selesai.

![Comment Section](manual-images/img-11-comment-section.png)

### Praktik Baik

- gunakan komentar yang jelas dan dapat ditindaklanjuti
- hindari komentar samar seperti please revise

---

## SOP 08 - Pemantauan Kedaluwarsa

Tujuan: Mencegah kontrak terlewat untuk perpanjangan dan mencegah lapse.

Cara alur ini berjalan:
- tinjau daftar Expiring Soon secara berkala
- prioritaskan kontrak dengan tanggal akhir terdekat
- buka setiap kontrak dan putuskan perpanjangan, penutupan, atau tindak lanjut

### Langkah

1. Buka halaman Expiring Soon.
2. Tinjau kontrak berdasarkan urgensi.
3. Buka setiap kontrak yang terdampak.
4. Koordinasikan tindakan perpanjangan atau penutupan.

![Expiring Soon](manual-images/img-12-expiring-soon.png)

### Jenis Pengingat

- expiry reminders
- pending signature reminders
- renewal notifications

---

## 6. Panduan Siklus Hidup Kontrak

Alur siklus hidup yang umum:
- Draft
- Submitted for Review
- Legal Review
- Approved
- Active
- Expiring Soon
- Expired

Kontrak yang terminated dikelola terpisah dan muncul pada menu Terminated.

### Catatan Tata Kelola Siklus Hidup

Tidak semua pengguna dapat memindahkan status di setiap tahap. Hak transisi status dikontrol oleh pengaturan peran dan permission.

---

## 7. Tanggung Jawab Berdasarkan Peran

| Role | Tanggung Jawab Umum | Batasan Umum |
|---|---|---|
| Contract Owner | Membuat kontrak, mengelola data, mengoordinasikan participant | Tidak dapat melakukan konfigurasi admin kecuali diberikan akses |
| Legal Reviewer | Review legal, meminta perbaikan, menyetujui kesiapan legal | Tidak dapat mengakses setup admin kecuali staff/admin |
| Business User | Mengisi field bisnis dan mengunggah dokumen terkait | Bisa memiliki hak transisi status yang terbatas |
| Signatory | Memberikan tanda tangan digital saat diminta | Secara default tidak memiliki hak edit yang lebih luas |
| Staff/Admin | Mengonfigurasi type, field, template, permission, pengaturan email | Harus mengikuti tata kelola dan kontrol perubahan |

---

## 8. Standar Layanan Dan Kontrol

### Standar Kualitas Data

- field wajib harus diisi sebelum pengajuan
- tanggal harus mengikuti logika kontraktual
- file yang diunggah harus terbaca dan relevan

### Standar Auditabilitas

- aksi penting harus dapat ditelusuri pada riwayat kontrak/audit log
- komunikasi kritis harus dilakukan melalui komentar

### Standar Kontrol Akses

- pengguna bertindak sesuai cakupan peran yang ditetapkan
- tombol yang tidak muncul biasanya menandakan keterbatasan permission

---

## 9. Panduan Troubleshooting

### Isu: Tidak Bisa Login

Kemungkinan penyebab:
- kredensial salah
- akun tidak aktif
- masalah sesi

Resolusi:
1. masukkan ulang kredensial dengan teliti
2. pastikan Caps Lock mati
3. hubungi administrator

### Isu: Kontrak Tidak Ditemukan

Kemungkinan penyebab:
- filter salah
- tidak punya akses ke kontrak
- keyword pencarian tidak sesuai

Resolusi:
1. hapus filter dan cari lagi
2. coba berdasarkan type kontrak dan tanggal
3. minta owner/admin untuk konfirmasi akses

### Isu: Validation Error Saat Submit Form

Kemungkinan penyebab:
- field wajib belum diisi
- format data salah
- tipe file tidak valid

Resolusi:
1. baca teks error di bawah field
2. lengkapi field wajib
3. unggah format file yang diizinkan

### Isu: Tombol Tidak Terlihat

Kemungkinan penyebab:
- pembatasan permission
- pembatasan berdasarkan status

Resolusi:
1. cek peran Anda
2. minta konfirmasi akses ke legal/admin

---

## 10. Pertanyaan Yang Sering Diajukan

### Q1. Apakah saya bisa mengedit kontrak setelah pengajuan?

Tergantung status saat ini dan peran permission Anda.

### Q2. Kenapa end date terisi otomatis pada beberapa form?

Beberapa tipe kontrak menggunakan logika start date ditambah durasi.

### Q3. Bagaimana saya tahu kontrak mana yang urgent?

Cek Expiring Soon dan indikator status pada tampilan list/detail.

### Q4. Di mana komentar legal harus ditulis?

Gunakan bagian komentar kontrak agar riwayat tetap dapat ditelusuri.

### Q5. Siapa yang bisa menggunakan Admin Panel?

Hanya pengguna staff/admin dengan permission yang diperlukan.

---

## 11. Glosarium

| Istilah | Arti |
|---|---|
| CLM | Contract Lifecycle Management |
| Dashboard | Halaman ringkasan utama setelah login |
| Structured Data | Field input dinamis khusus template |
| Participant | Orang yang ditugaskan dalam alur kerja kontrak |
| Draft | Tahap awal kontrak sebelum persetujuan penuh |
| Active | Tahap kontrak yang masih berlaku |
| Expiring Soon | Kontrak yang mendekati tanggal akhir |
| Terminated | Kontrak diakhiri lebih awal sebelum kedaluwarsa normal |
| Final Approved Document | Versi dokumen final yang diterima sebagai arsip |

---

## 12. Dukungan Dan Eskalasi

Jalur dukungan utama:
- Internal CLM Administrator

Eskalasi fungsional:
- Legal Team

Eskalasi teknis:
- System Support / IT Team

Saat mengajukan permintaan dukungan, sertakan:
- username
- nomor kontrak (jika relevan)
- nama layar
- pesan error yang jelas atau screenshot
- waktu kejadian

---

## 13. Panduan Ekspor PDF

Untuk menghasilkan PDF yang rapi dari buku panduan ini:

1. Buka markdown pada preview editor Anda.
2. Pastikan heading dan tabel tampil dengan benar.
3. Simpan screenshot di manual-images dengan nama file yang tercantum pada Lampiran C.
4. Ekspor ke PDF menggunakan tool markdown-to-PDF pilihan Anda.
5. Verifikasi page break dan alignment tabel.

Pengaturan cetak yang disarankan:
- kertas: A4
- margin: normal
- orientasi: portrait
- tampilkan header tabel pada page break jika didukung

---

## 14. Lampiran A: Kartu Quick Start

### Kartu 1 - Pengguna Harian

1. Login
2. Buka Dashboard
3. Periksa item urgent
4. Buka kontrak target
5. Perbarui komentar/dokumen/status
6. Logout

### Kartu 2 - Pembuat Kontrak

1. Create Contract
2. Lengkapi Langkah 1 sampai 4
3. Validasi field wajib
4. Submit
5. Pantau feedback review

### Kartu 3 - Legal Reviewer

1. Buka review queue/daftar kontrak
2. Baca detail dan dokumen
3. Tambahkan komentar legal
4. Minta revisi atau perbarui status

---

## 15. Lampiran B: Checklist Pra-Pengajuan

Gunakan checklist ini sebelum pengajuan final:

- semua field wajib sudah diisi
- jenis entitas legal dipilih dengan benar
- nama dan alamat pihak sudah diverifikasi
- start date dan end date sudah diverifikasi
- nilai kontrak sudah dicek
- dokumen pendukung yang wajib sudah diunggah
- peran participant sudah dicek
- komentar ditambahkan untuk kondisi khusus
- final review sudah selesai

---

## 16. Lampiran C: Indeks Screenshot Yang Disarankan

Ganti placeholder dengan file gambar final berikut:

1. img-01-login.png
2. img-02-dashboard.png
3. img-03-contract-list.png
4. img-04-wizard-step-1.png
5. img-05-wizard-step-2.png
6. img-06-wizard-step-3.png
7. img-07-wizard-step-4.png
8. img-08-contract-detail.png
9. img-09-participant-section.png
10. img-10-document-upload.png
11. img-11-comment-section.png
12. img-12-expiring-soon.png
13. img-13-admin-panel.png

---

Akhir buku panduan.
