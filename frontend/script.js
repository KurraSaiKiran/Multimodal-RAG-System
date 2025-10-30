class MultimodalRAG {
    constructor() {
        this.apiBase = 'http://localhost:5000/api';
        this.selectedFiles = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadStats();
        this.checkHealth();
    }

    setupEventListeners() {
        // File upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const clearBtn = document.getElementById('clearBtn');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        uploadBtn.addEventListener('click', this.uploadFiles.bind(this));
        clearBtn.addEventListener('click', this.clearFiles.bind(this));

        // Query
        const queryBtn = document.getElementById('queryBtn');
        const queryInput = document.getElementById('queryInput');
        
        queryBtn.addEventListener('click', this.queryDocuments.bind(this));
        queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                this.queryDocuments();
            }
        });

        // Stats
        const refreshStatsBtn = document.getElementById('refreshStatsBtn');
        const testSystemBtn = document.getElementById('testSystemBtn');
        refreshStatsBtn.addEventListener('click', this.loadStats.bind(this));
        testSystemBtn.addEventListener('click', this.testSystem.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
    }

    addFiles(files) {
        const validExtensions = ['.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf'];
        
        files.forEach(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            if (validExtensions.includes(ext)) {
                if (!this.selectedFiles.find(f => f.name === file.name)) {
                    this.selectedFiles.push(file);
                }
            } else {
                this.showToast(`File ${file.name} is not supported`, 'error');
            }
        });

        this.updateFileList();
        this.updateUploadButton();
    }

    updateFileList() {
        const container = document.getElementById('selectedFiles');
        container.innerHTML = '';

        this.selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileIcon = this.getFileIcon(file.name);
            
            fileItem.innerHTML = `
                <div class="file-info">
                    <i class="fas ${fileIcon} file-icon"></i>
                    <span>${file.name}</span>
                    <span class="file-size">(${this.formatFileSize(file.size)})</span>
                </div>
                <button class="remove-file" onclick="app.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            container.appendChild(fileItem);
        });
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const iconMap = {
            'pdf': 'fa-file-pdf',
            'txt': 'fa-file-alt',
            'md': 'fa-file-alt',
            'png': 'fa-file-image',
            'jpg': 'fa-file-image',
            'jpeg': 'fa-file-image'
        };
        return iconMap[ext] || 'fa-file';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileList();
        this.updateUploadButton();
    }

    clearFiles() {
        this.selectedFiles = [];
        this.updateFileList();
        this.updateUploadButton();
        document.getElementById('fileInput').value = '';
    }

    updateUploadButton() {
        const uploadBtn = document.getElementById('uploadBtn');
        uploadBtn.disabled = this.selectedFiles.length === 0;
    }

    async uploadFiles() {
        if (this.selectedFiles.length === 0) return;

        const formData = new FormData();
        this.selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        this.showProgress(true);
        
        try {
            const response = await fetch(`${this.apiBase}/upload/batch`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showUploadResult(result, 'success');
                this.showToast(`Successfully uploaded ${result.files.length} files`, 'success');
                this.clearFiles();
                this.loadStats();
            } else {
                this.showUploadResult(result, 'error');
                this.showToast(result.error || 'Upload failed', 'error');
            }
        } catch (error) {
            this.showUploadResult({ error: error.message }, 'error');
            this.showToast('Upload failed: ' + error.message, 'error');
        } finally {
            this.showProgress(false);
        }
    }

    showProgress(show) {
        const progressDiv = document.getElementById('uploadProgress');
        if (show) {
            progressDiv.style.display = 'block';
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;
                document.getElementById('progressFill').style.width = progress + '%';
                if (progress >= 90) clearInterval(interval);
            }, 200);
        } else {
            progressDiv.style.display = 'none';
            document.getElementById('progressFill').style.width = '0%';
        }
    }

    showUploadResult(result, type) {
        const resultDiv = document.getElementById('uploadResult');
        resultDiv.className = `result-${type}`;
        
        if (type === 'success') {
            resultDiv.innerHTML = `
                <h4><i class="fas fa-check-circle"></i> Upload Successful</h4>
                <p>${result.message}</p>
                <p><strong>Files processed:</strong> ${result.files.join(', ')}</p>
            `;
        } else {
            resultDiv.innerHTML = `
                <h4><i class="fas fa-exclamation-circle"></i> Upload Failed</h4>
                <p>${result.error}</p>
            `;
        }
    }

    async queryDocuments() {
        const queryInput = document.getElementById('queryInput');
        const contentFilter = document.getElementById('contentFilter');
        const query = queryInput.value.trim();

        if (!query) {
            this.showToast('Please enter a query', 'error');
            return;
        }

        this.showLoading(true);

        try {
            const requestBody = { query };
            if (contentFilter.value) {
                requestBody.content_type_filter = contentFilter.value;
            }

            const response = await fetch(`${this.apiBase}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showQueryResult(result);
                this.showToast('Query completed successfully', 'success');
            } else {
                this.showQueryError(result.error);
                this.showToast(result.error || 'Query failed', 'error');
            }
        } catch (error) {
            this.showQueryError(error.message);
            this.showToast('Query failed: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    showQueryResult(result) {
        const resultDiv = document.getElementById('queryResult');
        
        const html = `
            <div class="query-response">
                <h4><i class="fas fa-robot"></i> Response</h4>
                <p>${result.response}</p>
            </div>
            
            <div class="query-meta">
                <div class="meta-item">
                    <div class="meta-label">Query Type</div>
                    <div class="meta-value">${result.query_type}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Documents Retrieved</div>
                    <div class="meta-value">${result.retrieved_documents}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Context Used</div>
                    <div class="meta-value">${result.context_used}</div>
                </div>
            </div>
            
            ${result.sources && result.sources.length > 0 ? `
                <div class="sources-list">
                    <h4><i class="fas fa-link"></i> Sources</h4>
                    ${result.sources.map(source => `
                        <div class="source-item">
                            <div class="source-info">
                                <div class="source-name">${source.source}</div>
                                <div class="source-type">${source.content_type}</div>
                            </div>
                            <div class="relevance-score">${(source.relevance_score * 100).toFixed(1)}%</div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        `;
        
        resultDiv.innerHTML = html;
    }

    showQueryError(error) {
        const resultDiv = document.getElementById('queryResult');
        resultDiv.innerHTML = `
            <div class="result-error">
                <h4><i class="fas fa-exclamation-circle"></i> Query Failed</h4>
                <p>${error}</p>
            </div>
        `;
    }

    async loadStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('totalDocs').textContent = result.stats.total_documents;
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const result = await response.json();
            
            document.getElementById('systemStatus').textContent = 
                result.status === 'healthy' ? 'Healthy' : 'Unhealthy';
        } catch (error) {
            document.getElementById('systemStatus').textContent = 'Offline';
            this.showToast('Backend server is offline', 'error');
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    async testSystem() {
        try {
            // Add test document
            const response = await fetch(`${this.apiBase}/test/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Test document added successfully', 'success');
                
                // Test query
                setTimeout(async () => {
                    const queryResponse = await fetch(`${this.apiBase}/query`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query: 'What is machine learning?' })
                    });
                    
                    const queryResult = await queryResponse.json();
                    
                    if (queryResult.success) {
                        this.showQueryResult(queryResult);
                        this.showToast('System test completed successfully', 'success');
                    } else {
                        this.showToast('Query test failed: ' + queryResult.error, 'error');
                    }
                    
                    this.loadStats();
                }, 1000);
            } else {
                this.showToast('Test failed: ' + result.error, 'error');
            }
        } catch (error) {
            this.showToast('Test failed: ' + error.message, 'error');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
        
        toast.innerHTML = `
            <i class="fas ${icon}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize the application
const app = new MultimodalRAG();