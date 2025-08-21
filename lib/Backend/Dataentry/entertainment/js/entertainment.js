const supabaseUrl = 'https://cpuhivcyhvqayzgdvdaw.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdWhpdmN5aHZxYXl6Z2R2ZGF3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMzNDc4NDgsImV4cCI6MjA2ODkyMzg0OH0.dO22JLQjE7UeQHvQn6mojILNuWi_02MiZ9quz5v8pNk';
const supabaseClient = supabase.createClient(supabaseUrl, supabaseKey);

const form = document.getElementById('entertainmentForm');
const successMsg = document.getElementById('successMsg');
const errorMsg = document.getElementById('errorMsg');
const submitBtn = document.getElementById('submitBtn');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const coverInfo = document.getElementById('coverInfo');
const mediaInfo = document.getElementById('mediaInfo');

// Show file info
document.getElementById('cover_img').addEventListener('change', function(e) {
  if (this.files[0]) {
    coverInfo.textContent = `Selected: ${this.files[0].name} (${formatFileSize(this.files[0].size)})`;
  }
});

document.getElementById('media_file').addEventListener('change', function(e) {
  if (this.files[0]) {
    mediaInfo.textContent = `Selected: ${this.files[0].name} (${formatFileSize(this.files[0].size)})`;
  }
});

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

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  successMsg.textContent = '';
  errorMsg.textContent = '';
  submitBtn.disabled = true;
  progressContainer.style.display = 'block';
  
  const coverFile = document.getElementById('cover_img').files[0];
  const mediaFile = document.getElementById('media_file').files[0];

  if (!coverFile || !mediaFile) {
    errorMsg.textContent = "Please select both cover image and media file.";
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  // File size validation
  if (coverFile.size > 5 * 1024 * 1024) {
    errorMsg.textContent = "Cover image must be less than 5MB.";
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  if (mediaFile.size > 20 * 1024 * 1024) {
    errorMsg.textContent = "Media file must be less than 20MB.";
    submitBtn.disabled = false;
    progressContainer.style.display = 'none';
    return;
  }

  try {
    updateProgress(10);
    
    // Sanitize filenames
    const sanitize = (name) => name.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_\.-]/g, '');
    const coverPath = `covers/${Date.now()}_${sanitize(coverFile.name)}`;
    const mediaPath = `media/${Date.now()}_${sanitize(mediaFile.name)}`;

    // Upload cover image
    updateProgress(30);
    const { data: coverData, error: coverError } = await supabaseClient
      .storage.from('entertainment_media')
      .upload(coverPath, coverFile);

    if (coverError) {
      throw new Error(`Cover upload failed: ${coverError.message}`);
    }

    // Upload media file
    updateProgress(60);
    const { data: mediaData, error: mediaError } = await supabaseClient
      .storage.from('entertainment_media')
      .upload(mediaPath, mediaFile);

    if (mediaError) {
      // Try to delete the cover image if media upload fails
      await supabaseClient.storage.from('entertainment_media').remove([coverPath]);
      throw new Error(`Media upload failed: ${mediaError.message}`);
    }

    // Get public URLs
    updateProgress(80);
    const coverUrl = supabaseClient.storage.from('entertainment_media').getPublicUrl(coverPath).data.publicUrl;
    const mediaUrl = supabaseClient.storage.from('entertainment_media').getPublicUrl(mediaPath).data.publicUrl;

    // Insert record into table
    const entertainment = {
      title: form.title.value,
      type: form.type.value,
      description: form.description.value,
      cover_img_url: coverUrl,
      media_file_url: mediaUrl
    };

    const { data, error } = await supabaseClient
      .from('entertainments')
      .insert([entertainment]);

    if (error) {
      throw new Error(`Database insert failed: ${error.message}`);
    }

    updateProgress(100);
    successMsg.textContent = "Entertainment added successfully!";
    form.reset();
    coverInfo.textContent = '';
    mediaInfo.textContent = '';
    
    // Hide progress bar after success
    setTimeout(() => {
      progressContainer.style.display = 'none';
    }, 2000);
    
  } catch (error) {
    console.error(error);
    errorMsg.textContent = error.message;
    progressContainer.style.display = 'none';
  } finally {
    submitBtn.disabled = false;
  }
});
