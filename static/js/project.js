// Project page functionality

function showUploadModal() {
    openModal('uploadModal');
}

function closeUploadModal() {
    closeModal('uploadModal');
    document.getElementById('uploadForm').reset();
    document.getElementById('upload-progress').style.display = 'none';
}

// Handle file upload
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('file-upload');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show progress
            document.getElementById('upload-progress').style.display = 'block';
            document.querySelector('.modal-actions button[type="submit"]').disabled = true;
            
            try {
                const response = await fetch(`/project/${projectId}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Response status:', response.status);
                console.log('Response OK:', response.ok);
                
                const result = await response.json();
                console.log('Result:', result);
                
                if (response.ok && result.success) {
                    closeUploadModal();
                    
                    // Show analyzing message
                    const statusDiv = document.createElement('div');
                    statusDiv.className = 'alert alert-info';
                    statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing code... Please wait.';
                    document.querySelector('.project-container').insertBefore(statusDiv, document.querySelector('.project-stats-bar'));
                    
                    // Poll for analysis completion (check every 2 seconds for up to 30 seconds)
                    let attempts = 0;
                    const maxAttempts = 15;
                    
                    const checkAnalysis = setInterval(async () => {
                        attempts++;
                        
                        try {
                            const checkResponse = await fetch(`/api/file/${result.file_id}/status`);
                            const statusData = await checkResponse.json();
                            
                            if (statusData.analyzed || attempts >= maxAttempts) {
                                clearInterval(checkAnalysis);
                                window.location.reload();
                            }
                        } catch (err) {
                            console.error('Status check error:', err);
                            if (attempts >= maxAttempts) {
                                clearInterval(checkAnalysis);
                                window.location.reload();
                            }
                        }
                    }, 2000);
                    
                } else {
                    alert('Error: ' + (result.error || 'Upload failed'));
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Upload failed. Please try again.');
            } finally {
                document.getElementById('upload-progress').style.display = 'none';
                document.querySelector('.modal-actions button[type="submit"]').disabled = false;
            }
        });
    }
});
