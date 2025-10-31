/**
 * API Client for Blog Automation Dashboard
 */

const API_BASE_URL = '/api/v1';

const api = {
    /**
     * Generic API request handler
     */
    async request(method, endpoint, data = null) {
        const config = {
            method,
            url: `${API_BASE_URL}${endpoint}`,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (data) {
            if (method === 'GET') {
                config.params = data;
            } else {
                config.data = data;
            }
        }

        try {
            const response = await axios(config);
            return { success: true, data: response.data };
        } catch (error) {
            console.error('API Error:', error);
            const message = error.response?.data?.detail || error.message || 'An error occurred';
            return { success: false, error: message };
        }
    },

    /**
     * Workflow APIs
     */
    workflows: {
        // Get list of workflows
        async list(params = {}) {
            return api.request('GET', '/workflow/list', params);
        },

        // Get workflow status
        async getStatus(workflowId) {
            return api.request('GET', `/workflow/${workflowId}/status`);
        },

        // Start new workflow
        async start(data) {
            return api.request('POST', '/workflow/one-click-publish', data);
        },

        // Cancel workflow
        async cancel(workflowId) {
            return api.request('POST', `/workflow/${workflowId}/cancel`);
        },

        // Delete workflow
        async delete(workflowId) {
            return api.request('DELETE', `/workflow/${workflowId}`);
        },
    },

    /**
     * SEO APIs
     */
    seo: {
        // Analyze content
        async analyze(data) {
            return api.request('POST', '/seo/analyze', data);
        },

        // Analyze post
        async analyzePost(postId, saveScore = true) {
            return api.request('POST', `/seo/analyze-post/${postId}?save_score=${saveScore}`);
        },

        // Get SEO scores list
        async list(params = {}) {
            return api.request('GET', '/seo/scores', params);
        },

        // Get SEO score for post
        async getScore(postId) {
            return api.request('GET', `/seo/scores/${postId}`);
        },

        // Get SEO statistics
        async getStats() {
            return api.request('GET', '/seo/stats');
        },

        // Delete SEO score
        async delete(postId) {
            return api.request('DELETE', `/seo/scores/${postId}`);
        },
    },

    /**
     * Notification APIs
     */
    notifications: {
        // Get notification status
        async getStatus() {
            return api.request('GET', '/notifications/status');
        },

        // Send test notification
        async sendTest(data) {
            return api.request('POST', '/notifications/test', data);
        },

        // Test workflow complete notification
        async testWorkflowComplete() {
            return api.request('POST', '/notifications/test/workflow-complete');
        },

        // Test workflow failed notification
        async testWorkflowFailed() {
            return api.request('POST', '/notifications/test/workflow-failed');
        },
    },

    /**
     * Keyword APIs
     */
    keywords: {
        // Research keywords
        async research(data) {
            return api.request('POST', '/keywords/research', data);
        },

        // Get top keywords
        async getTop(limit = 20) {
            return api.request('GET', `/keywords/top?limit=${limit}`);
        },
    },

    /**
     * Content APIs
     */
    content: {
        // Generate content
        async generate(data) {
            return api.request('POST', '/content/generate', data);
        },

        // Get available LLM providers
        async getProviders() {
            return api.request('GET', '/content/llm-providers');
        },
    },

    /**
     * Analytics API
     */
    analytics: {
        // Get analytics status
        async getStatus() {
            return api.request('GET', '/analytics/status');
        },

        // Get overview metrics
        async getOverview(startDate = '30daysAgo', endDate = 'today') {
            return api.request('GET', '/analytics/overview', { start_date: startDate, end_date: endDate });
        },

        // Get realtime metrics
        async getRealtime() {
            return api.request('GET', '/analytics/realtime');
        },

        // Get traffic sources
        async getTrafficSources(startDate = '30daysAgo', endDate = 'today', limit = 10) {
            return api.request('GET', '/analytics/traffic-sources', {
                start_date: startDate,
                end_date: endDate,
                limit
            });
        },

        // Get top posts
        async getTopPosts(startDate = '30daysAgo', endDate = 'today', limit = 10) {
            return api.request('GET', '/analytics/top-posts', {
                start_date: startDate,
                end_date: endDate,
                limit
            });
        },

        // Get post performance
        async getPostPerformance(postPath, startDate = '30daysAgo', endDate = 'today') {
            return api.request('GET', `/analytics/post/${postPath}`, {
                start_date: startDate,
                end_date: endDate
            });
        },

        // Get comparison data
        async getComparison(currentStart = '30daysAgo', currentEnd = 'today', previousStart = '60daysAgo', previousEnd = '31daysAgo') {
            return api.request('GET', '/analytics/comparison', {
                current_start: currentStart,
                current_end: currentEnd,
                previous_start: previousStart,
                previous_end: previousEnd
            });
        }
    },

    /**
     * Health Check
     */
    async healthCheck() {
        return api.request('GET', '/health');
    },

    /**
     * Helper: Poll workflow status until completion
     */
    async pollWorkflowStatus(workflowId, onUpdate, interval = 2000) {
        const poll = async () => {
            const result = await api.workflows.getStatus(workflowId);

            if (result.success) {
                onUpdate(result.data);

                // Continue polling if still running
                if (result.data.status === 'running' || result.data.status === 'pending') {
                    setTimeout(poll, interval);
                }
            }
        };

        await poll();
    },

    /**
     * Helper: Format date
     */
    formatDate(dateString) {
        if (!dateString) return 'N/A';

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return '방금 전';
        if (diffMins < 60) return `${diffMins}분 전`;
        if (diffHours < 24) return `${diffHours}시간 전`;
        if (diffDays < 7) return `${diffDays}일 전`;

        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    /**
     * Helper: Format duration
     */
    formatDuration(seconds) {
        if (!seconds) return 'N/A';

        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);

        if (mins > 0) {
            return `${mins}분 ${secs}초`;
        }
        return `${secs}초`;
    },

    /**
     * Helper: Get status color
     */
    getStatusColor(status) {
        const colors = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'yellow',
        };
        return colors[status] || 'gray';
    },

    /**
     * Helper: Get grade color
     */
    getGradeColor(grade) {
        const colors = {
            'A+': 'green',
            'A': 'green',
            'B+': 'blue',
            'B': 'blue',
            'C+': 'yellow',
            'C': 'yellow',
            'D': 'orange',
            'F': 'red',
        };
        return colors[grade] || 'gray';
    },
};

// Make api globally available
window.api = api;
