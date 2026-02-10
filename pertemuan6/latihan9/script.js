document.getElementById('formPendaftaran').addEventListener('submit', function(event) {
    event.preventDefault(); // Supaya form nggak reload halaman
  
    alert('Data berhasil disimpan! Terima kasih sudah mendaftar.');
    
    // Setelah submit, form bisa dikosongkan (opsional)
    this.reset();
  });
  