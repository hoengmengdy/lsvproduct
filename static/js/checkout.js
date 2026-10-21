(() => {
  const modal = document.getElementById('address-modal');
  const form = document.getElementById('address-form');
  if (!modal || !form) return;
  const fields = form.elements;
  const province = fields.province_code;
  const district = fields.district_code;
  const commune = fields.commune_code;
  const save = form.querySelector('[type="submit"]');
  const error = document.getElementById('address-error');
  const title = document.getElementById('address-modal-title');
  const placeholders = new Map([province, district, commune].map(el => [el, el.options[0].text]));
  let locations;
  let loading;
  let saving = false;
  let openVersion = 0;
  const nameKey = form.dataset.language === 'km' ? 'name_km' : 'name';

  function fill(select, rows, selected = '') {
    select.replaceChildren(new Option(placeholders.get(select), ''));
    rows.forEach(row => select.add(new Option(row[nameKey], row.code)));
    select.disabled = rows.length === 0;
    select.value = selected;
  }
  function updateSave() {
    let phone = fields.phone.value.replace(/[\s()-]/g, '').replace(/^\+855/, '').replace(/^0/, '');
    fields.phone.setCustomValidity(!fields.phone.value || /^[1-9][0-9]{7,8}$/.test(phone) ? '' : form.dataset.phoneError);
    save.disabled = saving || !locations || [fields.first_name, fields.last_name, fields.phone, province, district, commune, fields.street].some(el => !el.value.trim() || !el.checkValidity());
  }
  async function loadLocations() {
    if (!loading) loading = fetch(form.dataset.locationsUrl).then(response => {
      if (!response.ok) throw new Error('Locations unavailable');
      return response.json();
    }).then(data => locations = data).catch(error => { loading = null; throw error; });
    return loading;
  }
  modal.addEventListener('show.bs.modal', async event => {
    const version = ++openVersion;
    const address = event.relatedTarget?.dataset.address ? JSON.parse(event.relatedTarget.dataset.address) : null;
    form.reset();
    fields.address_id.value = address?.id || '';
    error.hidden = true;
    saving = false;
    title.textContent = address ? form.dataset.editTitle : form.dataset.addTitle;
    for (const key of ['first_name', 'last_name', 'phone', 'street']) fields[key].value = address?.[key] || '';
    fields.phone.value = fields.phone.value.replace(/^\+855/, '');
    fields.is_default.checked = Boolean(address?.is_default);
    [province, district, commune].forEach(el => fill(el, []));
    updateSave();
    try {
      await loadLocations();
      if (version !== openVersion) return;
      fill(province, locations.province, address?.province_code);
      fill(district, locations.district.filter(row => row.parent === province.value), address?.district_code);
      fill(commune, locations.commune.filter(row => row.parent === district.value), address?.commune_code);
      updateSave();
    } catch (_) {
      error.textContent = form.dataset.locationError;
      error.hidden = false;
    }
  });
  modal.addEventListener('shown.bs.modal', () => fields.first_name.focus());
  province.addEventListener('change', () => {
    fill(district, locations.district.filter(row => row.parent === province.value));
    fill(commune, []);
    updateSave();
  });
  district.addEventListener('change', () => {
    fill(commune, locations.commune.filter(row => row.parent === district.value));
    updateSave();
  });
  form.addEventListener('input', updateSave);
  form.addEventListener('change', updateSave);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity() || save.disabled) return;
    saving = true;
    updateSave();
    error.hidden = true;
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form), headers: { 'Accept': 'application/json' } });
      if (response.redirected) { window.location.assign(response.url); return; }
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || form.dataset.error);
      const url = new URL(window.location.href);
      url.searchParams.set('address', data.address.id);
      window.location.assign(url);
    } catch (failure) {
      error.textContent = failure.message || form.dataset.error;
      error.hidden = false;
      saving = false;
      updateSave();
    }
  });
})();
