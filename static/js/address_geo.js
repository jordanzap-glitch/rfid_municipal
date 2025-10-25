document.addEventListener('DOMContentLoaded', function() {
    const provinceSelect = document.getElementById('province');
    const municipalitySelect = document.getElementById('municipality');
    const barangaySelect = document.getElementById('barangay');

    // Helper to load municipalities for a province
    function loadMunicipalities(provinceId, callback) {
        municipalitySelect.innerHTML = '<option value="">-- select municipality --</option>';
        barangaySelect.innerHTML = '<option value="">-- select barangay --</option>';
        if (provinceId) {
            fetch(`/ajax/municipalities/?province_id=${provinceId}`)
                .then(response => response.json())
                .then(data => {
                    let firstMunicipalityId = null;
                    data.forEach((m, idx) => {
                        const opt = document.createElement('option');
                        opt.value = m.id;
                        opt.textContent = m.municipality_name;
                        municipalitySelect.appendChild(opt);
                        if (idx === 0) firstMunicipalityId = m.id;
                    });
                    if (firstMunicipalityId) {
                        municipalitySelect.value = firstMunicipalityId;
                        if (callback) callback(firstMunicipalityId);
                    }
                });
        }
    }

    // Helper to load barangays for a municipality
    function loadBarangays(municipalityId) {
        barangaySelect.innerHTML = '<option value="">-- select barangay --</option>';
        if (municipalityId) {
            fetch(`/ajax/barangays/?municipality_id=${municipalityId}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(b => {
                        const opt = document.createElement('option');
                        opt.value = b.id;
                        opt.textContent = b.barangay_name;
                        barangaySelect.appendChild(opt);
                    });
                    // Optionally select first barangay
                    if (data.length > 0) {
                        barangaySelect.value = data[0].id;
                    }
                });
        }
    }

    // On province change
    provinceSelect.addEventListener('change', function() {
        const provinceId = this.value;
        loadMunicipalities(provinceId, loadBarangays);
    });

    // On municipality change
    municipalitySelect.addEventListener('change', function() {
        const municipalityId = this.value;
        loadBarangays(municipalityId);
    });

    // On page load, set province to 1 and load municipalities/barangays
    if (provinceSelect.value === "1") {
        loadMunicipalities("1", loadBarangays);
    }
});