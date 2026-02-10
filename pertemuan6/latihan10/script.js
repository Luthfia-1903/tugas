document.addEventListener('DOMContentLoaded', function() {
    const formPembayaran = document.getElementById('formPembayaran');
    
    // Validasi input NIK - hanya angka yang diperbolehkan
    const nikInput = document.getElementById('nik');
    nikInput.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9]/g, '');
    });
    
    // Update jumlah pembayaran otomatis berdasarkan tujuan
    const tujuanSelect = document.getElementById('tujuan');
    const jumlahInput = document.getElementById('jumlah');
    
    tujuanSelect.addEventListener('change', function() {
        switch(this.value) {
            case 'pendaftaran':
                jumlahInput.value = 500000;
                break;
            case 'registrasi':
                jumlahInput.value = 250000;
                break;
            case 'spp':
                jumlahInput.value = 3500000;
                break;
            case 'ujian':
                jumlahInput.value = 150000;
                break;
            case 'wisuda':
                jumlahInput.value = 1500000;
                break;
            default:
                jumlahInput.value = '';
        }
    });
    
    // Validasi form saat submit
    formPembayaran.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validasi NIK
        const nik = nikInput.value;
        if (nik.length !== 16) {
            showError('NIK harus terdiri dari 16 digit angka!');
            nikInput.focus();
            return;
        }
        
        // Validasi nama lengkap
        const nama = document.getElementById('nama').value;
        if (nama.trim() === '') {
            showError('Nama lengkap tidak boleh kosong!');
            return;
        }
        
        // Validasi tujuan pembayaran
        if (tujuanSelect.value === '') {
            showError('Silakan pilih tujuan pembayaran!');
            return;
        }
        
        // Validasi jumlah pembayaran
        const jumlah = jumlahInput.value;
        if (jumlah <= 0) {
            showError('Jumlah pembayaran harus lebih dari 0!');
            return;
        }
        
        // Validasi metode pembayaran
        const metodePembayaran = document.querySelector('input[name="metode_pembayaran"]:checked');
        if (!metodePembayaran) {
            showError('Silakan pilih metode pembayaran!');
            return;
        }
        
        // Validasi bukti pembayaran
        const buktiFile = document.getElementById('bukti').files[0];
        if (!buktiFile) {
            showError('Silakan unggah bukti pembayaran!');
            return;
        }
        
        // Validasi ukuran file
        if (buktiFile.size > 5 * 1024 * 1024) {
            showError('Ukuran file bukti pembayaran tidak boleh lebih dari 5MB!');
            return;
        }
        
        // Validasi tipe file
        const validTypes = ['image/jpeg', 'image/png', 'application/pdf'];
        if (!validTypes.includes(buktiFile.type)) {
            showError('Format file bukti pembayaran harus JPG, PNG, atau PDF!');
            return;
        }
        
        // Jika semua validasi berhasil
        saveFormData();
    });
    
    // Fungsi untuk menampilkan pesan error
    function showError(message) {
        alert(message);
    }
    
    // Fungsi untuk menyimpan data form
    function saveFormData() {
        // Di sini Anda bisa mengimplementasikan kode untuk mengirim data ke server
        // Untuk contoh sederhana, kita hanya menampilkan pesan sukses
        
        const tujuanText = tujuanSelect.options[tujuanSelect.selectedIndex].text;
        const metodePembayaranValue = document.querySelector('input[name="metode_pembayaran"]:checked').value;
        let namaBank = '';
        
        switch(metodePembayaranValue) {
            case 'bsi':
                namaBank = 'Bank Syariah Indonesia (BSI)';
                break;
            case 'bmi':
                namaBank = 'Bank Muamalat Indonesia (BMI)';
                break;
            case 'bms':
                namaBank = 'Bank Mega Syariah (BMS)';
                break;
        }
        
        // Menampilkan ringkasan pembayaran
        const confirmMessage = `
            Pembayaran berhasil disimpan!
            
            Detail Pembayaran:
            - Nama: ${document.getElementById('nama').value}
            - NIK: ${document.getElementById('nik').value}
            - Tujuan: ${tujuanText}
            - Jumlah: Rp${formatNumber(document.getElementById('jumlah').value)}
            - Metode: ${namaBank}
            
            Terima kasih telah melakukan pembayaran.
        `;
        
        alert(confirmMessage);
        formPembayaran.reset();
    }
    
    // Fungsi untuk memformat angka dengan separator ribuan
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }
});