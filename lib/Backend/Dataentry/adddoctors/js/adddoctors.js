// --- Supabase setup ---
const supabaseUrl = 'https://cpuhivcyhvqayzgdvdaw.supabase.co';
const supabaseKey =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

// --- DOM refs ---
const form = document.getElementById('doctorForm');
const successMsg = document.getElementById('successMsg');
const errorMsg = document.getElementById('errorMsg');
const submitBtn = document.getElementById('submitBtn');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const profileInfo = document.getElementById('profileInfo');
const profileInput = document.getElementById('profile_picture');

// --- Helpers ---
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function updateProgress(percent) {
  progressContainer.style.display = 'block';
  progressBar.style.width = percent + '%';
  progressBar.textContent = percent + '%';
}

function sanitize(name) {
  return name.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_.-]/g, '');
}

function clearAlerts() {
  successMsg.textContent = '';
  errorMsg.textContent = '';
  successMsg.style.display = 'none';
  errorMsg.style.display = 'none';
}

function showSuccess(text) {
  successMsg.textContent = text;
  successMsg.style.display = 'block';
  errorMsg.style.display = 'none';
  successMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showError(text) {
  errorMsg.textContent = text;
  errorMsg.style.display = 'block';
  successMsg.style.display = 'none';
  errorMsg.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// --- UI: show file info ---
profileInput.addEventListener('change', function () {
  if (this.files && this.files[0]) {
    profileInfo.textContent = `Selected: ${this.files[0].name} (${formatFileSize(
      this.files[0].size
    )})`;
  } else {
    profileInfo.textContent = '';
  }
});

// --- Submit handler ---
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearAlerts();

  submitBtn.disabled = true;
  progressContainer.style.display = 'block';

  const profileFile = profileInput.files[0];

  // Basic validations
  if (!profileFile) {
    showError('Please select a profile picture.');
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  // Type check (don't rely only on accept="image/*")
  if (!profileFile.type || !profileFile.type.startsWith('image/')) {
    showError('Only image files are allowed (PNG or JPG).');
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  // Size check
  if (profileFile.size > 5 * 1024 * 1024) {
    showError('Profile picture must be less than 5MB.');
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  try {
    updateProgress(10);

    // Upload to Storage
    const profilePath = `profiles/${Date.now()}_${sanitize(profileFile.name)}`;
    updateProgress(30);
    const { error: profileError } = await supabaseClient
      .storage.from('doctor_profiles')
      .upload(profilePath, profileFile);

    if (profileError) throw new Error(`Profile picture upload failed: ${profileError.message}`);

    // Public URL
    updateProgress(60);
    const profileUrl = supabaseClient.storage
      .from('doctor_profiles')
      .getPublicUrl(profilePath).data.publicUrl;

    // Insert DB row
    const doctor = {
      name: form.name.value,
      email: form.email.value,
      phone: form.phone.value,
      category: form.category.value,
      profilepicture: profileUrl,
    };

    const { error } = await supabaseClient.from('doctors').insert([doctor]);
    if (error) {
      // cleanup file if DB insert fails
      await supabaseClient.storage.from('doctor_profiles').remove([profilePath]);
      throw new Error(`Database insert failed: ${error.message}`);
    }

    updateProgress(100);
    showSuccess('Doctor details added successfully!');
    form.reset();
    profileInfo.textContent = '';

    setTimeout(() => {
      progressContainer.style.display = 'none';
      updateProgress(0);
    }, 1500);
  } catch (err) {
    console.error(err);
    showError(err.message);
    progressContainer.style.display = 'none';
  } finally {
    submitBtn.disabled = false;
  }
});
