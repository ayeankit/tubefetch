class YouTubeDashboard {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.currentQuery = '';
        this.isSearchMode = false;
        
        this.initializeEventListeners();
        this.loadStats();
        this.loadVideos();
    }

    initializeEventListeners() {
        // Fetch videos button
        document.getElementById('fetchVideosBtn').addEventListener('click', () => {
            this.fetchNewVideos();
        });

        // Search button
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.performSearch();
        });

        // Clear button
        document.getElementById('clearBtn').addEventListener('click', () => {
            this.clearSearch();
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });

        // Search input enter key
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // Per page select
        document.getElementById('perPageSelect').addEventListener('change', (e) => {
            this.perPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadVideos();
        });
    }

    showLoading() {
        document.getElementById('loadingIndicator').style.display = 'block';
    }

    hideLoading() {
        document.getElementById('loadingIndicator').style.display = 'none';
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alertElement = document.getElementById(alertId);
            if (alertElement) {
                const bsAlert = new bootstrap.Alert(alertElement);
                bsAlert.close();
            }
        }, 5000);
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            
            document.getElementById('totalVideos').textContent = data.total_videos.toLocaleString();
            document.getElementById('latestVideo').textContent = 
                data.latest_published ? new Date(data.latest_published).toLocaleDateString() : 'N/A';
            document.getElementById('oldestVideo').textContent = 
                data.oldest_published ? new Date(data.oldest_published).toLocaleDateString() : 'N/A';
        } catch (error) {
            console.error('Error loading stats:', error.message || error);
            // Set fallback values
            document.getElementById('totalVideos').textContent = 'Error';
            document.getElementById('latestVideo').textContent = 'Error';
            document.getElementById('oldestVideo').textContent = 'Error';
        }
    }

    async loadVideos(page = 1) {
        this.showLoading();
        this.currentPage = page;
        
        try {
            let url;
            if (this.isSearchMode && this.currentQuery) {
                url = `/api/videos/search?q=${encodeURIComponent(this.currentQuery)}&page=${page}&per_page=${this.perPage}`;
            } else {
                url = `/api/videos?page=${page}&per_page=${this.perPage}`;
            }
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            
            this.renderVideos(data.videos);
            this.renderPagination(data.pagination);
        } catch (error) {
            console.error('Error loading videos:', error.message || error);
            this.showAlert(`Error loading videos: ${error.message || 'Network error'}`, 'danger');
            this.renderVideos([]);
        } finally {
            this.hideLoading();
        }
    }

    async fetchNewVideos() {
        const query = document.getElementById('queryInput').value.trim() || 'programming';
        const fetchBtn = document.getElementById('fetchVideosBtn');
        
        // Disable button and show loading
        fetchBtn.disabled = true;
        fetchBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Fetching...';
        
        try {
            const response = await fetch('/api/videos/fetch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query, max_results: 50 })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showAlert(
                    `Successfully fetched ${data.total_fetched} videos, stored ${data.stored_count} new videos for query "${data.query}"`,
                    'success'
                );
                this.loadStats();
                this.loadVideos();
            } else {
                this.showAlert(data.error || 'Error fetching videos', 'danger');
            }
        } catch (error) {
            console.error('Error fetching videos:', error);
            this.showAlert('Network error while fetching videos', 'danger');
        } finally {
            // Re-enable button
            fetchBtn.disabled = false;
            fetchBtn.innerHTML = '<i class="fas fa-download me-1"></i>Fetch New Videos';
        }
    }

    performSearch() {
        const searchQuery = document.getElementById('searchInput').value.trim();
        
        if (!searchQuery) {
            this.showAlert('Please enter a search query', 'warning');
            return;
        }
        
        this.currentQuery = searchQuery;
        this.isSearchMode = true;
        this.currentPage = 1;
        this.loadVideos();
    }

    clearSearch() {
        document.getElementById('searchInput').value = '';
        this.currentQuery = '';
        this.isSearchMode = false;
        this.currentPage = 1;
        this.loadVideos();
    }

    refreshData() {
        this.loadStats();
        this.loadVideos();
    }

    renderVideos(videos) {
        const container = document.getElementById('videosContainer');
        
        if (!videos || videos.length === 0) {
            container.innerHTML = `
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center py-5">
                            <i class="fas fa-video fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">No videos found</h4>
                            <p class="text-muted">
                                ${this.isSearchMode ? 
                                    'Try adjusting your search query or clear the search to view all videos.' : 
                                    'Click "Fetch New Videos" to load videos from YouTube.'
                                }
                            </p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }
        
        const videosHtml = videos.map(video => this.renderVideoCard(video)).join('');
        container.innerHTML = videosHtml;
    }

    renderVideoCard(video) {
        const publishedDate = new Date(video.published_at).toLocaleDateString();
        const publishedTime = new Date(video.published_at).toLocaleTimeString();
        const thumbnail = video.thumbnails.medium || video.thumbnails.default || '/static/placeholder.svg';
        const videoUrl = `https://www.youtube.com/watch?v=${video.video_id}`;
        
        // Truncate description
        const maxDescLength = 150;
        const description = video.description && video.description.length > maxDescLength
            ? video.description.substring(0, maxDescLength) + '...'
            : video.description || 'No description available';
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100">
                    <div class="position-relative">
                        <img src="${thumbnail}" class="card-img-top" alt="${video.title}" 
                             style="height: 200px; object-fit: cover;">
                        <div class="position-absolute top-0 end-0 m-2">
                            <span class="badge bg-dark">${video.duration || 'N/A'}</span>
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h6 class="card-title" title="${video.title}">
                            ${video.title.length > 60 ? video.title.substring(0, 60) + '...' : video.title}
                        </h6>
                        <p class="card-text text-muted small flex-grow-1">
                            ${description}
                        </p>
                        <div class="mt-auto">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <small class="text-muted">
                                    <i class="fas fa-user me-1"></i>
                                    ${video.channel_title || 'Unknown Channel'}
                                </small>
                                ${video.view_count ? `
                                    <small class="text-muted">
                                        <i class="fas fa-eye me-1"></i>
                                        ${this.formatNumber(video.view_count)}
                                    </small>
                                ` : ''}
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    <i class="fas fa-calendar me-1"></i>
                                    ${publishedDate}
                                </small>
                                <a href="${videoUrl}" target="_blank" class="btn btn-sm btn-outline-danger">
                                    <i class="fab fa-youtube me-1"></i>
                                    Watch
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderPagination(pagination) {
        const container = document.getElementById('paginationContainer');
        const list = document.getElementById('paginationList');
        
        if (!pagination || pagination.pages <= 1) {
            container.style.display = 'none';
            return;
        }
        
        container.style.display = 'block';
        
        let paginationHtml = '';
        
        // Previous button
        if (pagination.has_prev) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.prev_page}">
                        <i class="fas fa-chevron-left"></i>
                    </a>
                </li>
            `;
        } else {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link">
                        <i class="fas fa-chevron-left"></i>
                    </span>
                </li>
            `;
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        if (startPage > 1) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
            if (startPage > 2) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            if (i === pagination.page) {
                paginationHtml += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
            }
        }
        
        if (endPage < pagination.pages) {
            if (endPage < pagination.pages - 1) {
                paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.pages}">${pagination.pages}</a></li>`;
        }
        
        // Next button
        if (pagination.has_next) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.next_page}">
                        <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
            `;
        } else {
            paginationHtml += `
                <li class="page-item disabled">
                    <span class="page-link">
                        <i class="fas fa-chevron-right"></i>
                    </span>
                </li>
            `;
        }
        
        list.innerHTML = paginationHtml;
        
        // Add click event listeners
        list.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.closest('a').getAttribute('data-page'));
                this.loadVideos(page);
            });
        });
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeDashboard();
});
