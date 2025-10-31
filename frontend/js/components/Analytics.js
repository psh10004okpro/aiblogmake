/**
 * Analytics Component
 *
 * Displays Google Analytics data with charts and visualizations.
 */
export default {
    name: 'Analytics',

    data() {
        return {
            status: null,
            overview: null,
            realtime: null,
            trafficSources: [],
            topPosts: [],
            comparison: null,
            loading: false,
            error: null,

            // Date range
            dateRange: {
                start: '30daysAgo',
                end: 'today'
            },

            // Charts
            overviewChart: null,
            trafficChart: null,
            postsChart: null,

            // Refresh interval
            refreshInterval: null,
            autoRefresh: true,
            refreshRate: 300000  // 5 minutes
        };
    },

    computed: {
        isConfigured() {
            return this.status && this.status.configured;
        },

        dateRangeOptions() {
            return [
                { value: '7daysAgo', label: '최근 7일' },
                { value: '30daysAgo', label: '최근 30일' },
                { value: '90daysAgo', label: '최근 90일' }
            ];
        },

        totalTrafficSessions() {
            return this.trafficSources.reduce((sum, source) => sum + source.sessions, 0);
        }
    },

    async mounted() {
        await this.loadStatus();

        if (this.isConfigured) {
            await this.loadAllData();
            this.initCharts();

            if (this.autoRefresh) {
                this.startAutoRefresh();
            }
        }
    },

    beforeUnmount() {
        this.destroyCharts();
        this.stopAutoRefresh();
    },

    methods: {
        async loadStatus() {
            try {
                const response = await api.analytics.getStatus();
                this.status = response.data;
            } catch (error) {
                console.error('Failed to load analytics status:', error);
                this.status = { configured: false };
            }
        },

        async loadAllData() {
            this.loading = true;
            this.error = null;

            try {
                await Promise.all([
                    this.loadOverview(),
                    this.loadRealtime(),
                    this.loadTrafficSources(),
                    this.loadTopPosts(),
                    this.loadComparison()
                ]);
            } catch (error) {
                console.error('Failed to load analytics data:', error);
                this.error = 'Analytics 데이터를 불러오는데 실패했습니다.';
                this.$emit('show-toast', {
                    message: 'Analytics 데이터 로드 실패',
                    type: 'error'
                });
            } finally {
                this.loading = false;
            }
        },

        async loadOverview() {
            try {
                const response = await api.analytics.getOverview(
                    this.dateRange.start,
                    this.dateRange.end
                );
                this.overview = response.data;
            } catch (error) {
                console.error('Failed to load overview:', error);
            }
        },

        async loadRealtime() {
            try {
                const response = await api.analytics.getRealtime();
                this.realtime = response.data;
            } catch (error) {
                console.error('Failed to load realtime:', error);
            }
        },

        async loadTrafficSources() {
            try {
                const response = await api.analytics.getTrafficSources(
                    this.dateRange.start,
                    this.dateRange.end,
                    10
                );
                this.trafficSources = response.data.sources;

                // Update traffic chart
                if (this.trafficChart) {
                    this.updateTrafficChart();
                }
            } catch (error) {
                console.error('Failed to load traffic sources:', error);
            }
        },

        async loadTopPosts() {
            try {
                const response = await api.analytics.getTopPosts(
                    this.dateRange.start,
                    this.dateRange.end,
                    10
                );
                this.topPosts = response.data.posts;

                // Update posts chart
                if (this.postsChart) {
                    this.updatePostsChart();
                }
            } catch (error) {
                console.error('Failed to load top posts:', error);
            }
        },

        async loadComparison() {
            try {
                // Calculate previous period based on current range
                const previousStart = this.dateRange.start === '7daysAgo' ? '14daysAgo' :
                                     this.dateRange.start === '30daysAgo' ? '60daysAgo' :
                                     '180daysAgo';

                const previousEnd = this.dateRange.start === '7daysAgo' ? '8daysAgo' :
                                   this.dateRange.start === '30daysAgo' ? '31daysAgo' :
                                   '91daysAgo';

                const response = await api.analytics.getComparison(
                    this.dateRange.start,
                    this.dateRange.end,
                    previousStart,
                    previousEnd
                );
                this.comparison = response.data;

                // Update overview chart
                if (this.overviewChart) {
                    this.updateOverviewChart();
                }
            } catch (error) {
                console.error('Failed to load comparison:', error);
            }
        },

        initCharts() {
            this.initOverviewChart();
            this.initTrafficChart();
            this.initPostsChart();
        },

        initOverviewChart() {
            const canvas = this.$refs.overviewChart;
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            this.overviewChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['이전 기간', '현재 기간'],
                    datasets: [
                        {
                            label: '페이지뷰',
                            data: [],
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: '세션',
                            data: [],
                            borderColor: 'rgb(16, 185, 129)',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: '사용자',
                            data: [],
                            borderColor: 'rgb(139, 92, 246)',
                            backgroundColor: 'rgba(139, 92, 246, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: '트래픽 추이',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            this.updateOverviewChart();
        },

        updateOverviewChart() {
            if (!this.overviewChart || !this.comparison) return;

            const current = this.comparison.current_period.metrics;
            const previous = this.comparison.previous_period.metrics;

            this.overviewChart.data.datasets[0].data = [previous.page_views, current.page_views];
            this.overviewChart.data.datasets[1].data = [previous.sessions, current.sessions];
            this.overviewChart.data.datasets[2].data = [previous.users, current.users];

            this.overviewChart.update();
        },

        initTrafficChart() {
            const canvas = this.$refs.trafficChart;
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            this.trafficChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(20, 184, 166, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(107, 114, 128, 0.8)',
                            'rgba(99, 102, 241, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: '트래픽 소스',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    }
                }
            });

            this.updateTrafficChart();
        },

        updateTrafficChart() {
            if (!this.trafficChart) return;

            const labels = this.trafficSources.map(s => `${s.source} (${s.medium})`);
            const data = this.trafficSources.map(s => s.sessions);

            this.trafficChart.data.labels = labels;
            this.trafficChart.data.datasets[0].data = data;

            this.trafficChart.update();
        },

        initPostsChart() {
            const canvas = this.$refs.postsChart;
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            this.postsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: '페이지뷰',
                        data: [],
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: '인기 포스트 TOP 10',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });

            this.updatePostsChart();
        },

        updatePostsChart() {
            if (!this.postsChart) return;

            const labels = this.topPosts.map(p =>
                p.page_title.length > 40 ? p.page_title.substring(0, 40) + '...' : p.page_title
            );
            const data = this.topPosts.map(p => p.page_views);

            this.postsChart.data.labels = labels;
            this.postsChart.data.datasets[0].data = data;

            this.postsChart.update();
        },

        destroyCharts() {
            if (this.overviewChart) {
                this.overviewChart.destroy();
                this.overviewChart = null;
            }

            if (this.trafficChart) {
                this.trafficChart.destroy();
                this.trafficChart = null;
            }

            if (this.postsChart) {
                this.postsChart.destroy();
                this.postsChart = null;
            }
        },

        async changeDateRange(range) {
            this.dateRange.start = range;
            await this.loadAllData();
        },

        async refresh() {
            await this.loadAllData();
            this.$emit('show-toast', {
                message: 'Analytics 데이터가 새로고침되었습니다.',
                type: 'success'
            });
        },

        startAutoRefresh() {
            this.refreshInterval = setInterval(() => {
                this.loadRealtime();
            }, this.refreshRate);
        },

        stopAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
        },

        toggleAutoRefresh() {
            this.autoRefresh = !this.autoRefresh;

            if (this.autoRefresh) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        },

        formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'M';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'K';
            }
            return num.toString();
        },

        formatDuration(seconds) {
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        },

        getChangeClass(change) {
            if (!change) return '';
            return change.percentage > 0 ? 'text-green-600' : change.percentage < 0 ? 'text-red-600' : 'text-gray-600';
        },

        getChangeIcon(change) {
            if (!change) return '';
            return change.percentage > 0 ? 'fa-arrow-up' : change.percentage < 0 ? 'fa-arrow-down' : 'fa-minus';
        }
    },

    template: `
        <div class="analytics-container">
            <!-- Page Header -->
            <div class="flex items-center justify-between mb-8">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900 mb-2">Google Analytics</h1>
                    <p class="text-gray-600">블로그 성과 측정 및 분석</p>
                </div>

                <div class="flex gap-3">
                    <select
                        v-model="dateRange.start"
                        @change="changeDateRange(dateRange.start)"
                        class="input"
                        :disabled="!isConfigured"
                    >
                        <option
                            v-for="option in dateRangeOptions"
                            :key="option.value"
                            :value="option.value"
                        >
                            {{ option.label }}
                        </option>
                    </select>

                    <button
                        @click="refresh"
                        :disabled="!isConfigured || loading"
                        class="btn btn-primary"
                    >
                        <i class="fas" :class="loading ? 'fa-spinner fa-spin' : 'fa-sync-alt'"></i>
                        새로고침
                    </button>
                </div>
            </div>

            <!-- Not Configured Warning -->
            <div v-if="!isConfigured" class="card mb-8">
                <div class="card-content">
                    <div class="flex items-start gap-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                        <i class="fas fa-exclamation-triangle text-yellow-600 text-2xl mt-1"></i>
                        <div class="flex-1">
                            <h3 class="font-semibold text-yellow-900 mb-2">
                                Google Analytics가 설정되지 않았습니다
                            </h3>
                            <p class="text-sm text-yellow-800 mb-3">
                                Analytics 기능을 사용하려면 .env 파일에서 다음 설정을 구성하세요:
                            </p>
                            <div class="bg-yellow-100 p-3 rounded font-mono text-xs overflow-x-auto">
                                <pre># Google Analytics 4 설정
GA_PROPERTY_ID=your-property-id
GA_CREDENTIALS_PATH=/path/to/service-account.json</pre>
                            </div>
                            <p class="text-sm text-yellow-800 mt-3">
                                자세한 설정 방법은 <a href="/docs/ANALYTICS.md" target="_blank" class="underline font-medium">Analytics 문서</a>를 참조하세요.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="loading && isConfigured" class="text-center py-12">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">Analytics 데이터 로딩 중...</p>
            </div>

            <!-- Analytics Data -->
            <div v-else-if="isConfigured" class="space-y-6">
                <!-- Realtime Stats -->
                <div v-if="realtime" class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold flex items-center gap-2">
                            <i class="fas fa-circle text-red-600 animate-pulse"></i>
                            실시간 방문자
                        </h2>
                        <span class="text-sm text-gray-600">
                            {{ new Date(realtime.timestamp).toLocaleTimeString('ko-KR') }}
                        </span>
                    </div>
                    <div class="card-content">
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div class="text-center">
                                <div class="text-5xl font-bold text-blue-600 mb-2">
                                    {{ realtime.active_users }}
                                </div>
                                <div class="text-gray-600">현재 활성 사용자</div>
                            </div>

                            <div v-if="realtime.active_users_by_device.length > 0">
                                <div class="text-sm font-semibold text-gray-700 mb-2">디바이스별</div>
                                <div class="space-y-2">
                                    <div
                                        v-for="device in realtime.active_users_by_device"
                                        :key="device.device"
                                        class="flex justify-between"
                                    >
                                        <span class="text-gray-600">{{ device.device }}</span>
                                        <span class="font-semibold">{{ device.active_users }}</span>
                                    </div>
                                </div>
                            </div>

                            <div v-if="realtime.active_users_by_country.length > 0">
                                <div class="text-sm font-semibold text-gray-700 mb-2">국가별 (Top 5)</div>
                                <div class="space-y-2">
                                    <div
                                        v-for="country in realtime.active_users_by_country.slice(0, 5)"
                                        :key="country.country"
                                        class="flex justify-between"
                                    >
                                        <span class="text-gray-600">{{ country.country }}</span>
                                        <span class="font-semibold">{{ country.active_users }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Overview Metrics -->
                <div v-if="overview" class="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div class="stat-card">
                        <div class="stat-icon bg-blue-100">
                            <i class="fas fa-eye text-blue-600"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-label">페이지뷰</div>
                            <div class="stat-value">{{ formatNumber(overview.metrics.page_views) }}</div>
                            <div v-if="comparison" :class="getChangeClass(comparison.changes.page_views)" class="text-sm font-medium">
                                <i class="fas" :class="getChangeIcon(comparison.changes.page_views)"></i>
                                {{ Math.abs(comparison.changes.page_views.percentage).toFixed(1) }}%
                            </div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-green-100">
                            <i class="fas fa-users text-green-600"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-label">사용자</div>
                            <div class="stat-value">{{ formatNumber(overview.metrics.users) }}</div>
                            <div v-if="comparison" :class="getChangeClass(comparison.changes.users)" class="text-sm font-medium">
                                <i class="fas" :class="getChangeIcon(comparison.changes.users)"></i>
                                {{ Math.abs(comparison.changes.users.percentage).toFixed(1) }}%
                            </div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-purple-100">
                            <i class="fas fa-chart-line text-purple-600"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-label">참여율</div>
                            <div class="stat-value">{{ overview.metrics.engagement_rate.toFixed(1) }}%</div>
                            <div v-if="comparison" :class="getChangeClass(comparison.changes.engagement_rate)" class="text-sm font-medium">
                                <i class="fas" :class="getChangeIcon(comparison.changes.engagement_rate)"></i>
                                {{ Math.abs(comparison.changes.engagement_rate.percentage).toFixed(1) }}%
                            </div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon bg-yellow-100">
                            <i class="fas fa-clock text-yellow-600"></i>
                        </div>
                        <div class="stat-content">
                            <div class="stat-label">평균 세션 시간</div>
                            <div class="stat-value">{{ formatDuration(overview.metrics.avg_session_duration) }}</div>
                            <div class="text-sm text-gray-600">
                                이탈률: {{ overview.metrics.bounce_rate.toFixed(1) }}%
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Overview Trend Chart -->
                    <div class="card">
                        <div class="card-content">
                            <div style="height: 300px;">
                                <canvas ref="overviewChart"></canvas>
                            </div>
                        </div>
                    </div>

                    <!-- Traffic Sources Chart -->
                    <div class="card">
                        <div class="card-content">
                            <div style="height: 300px;">
                                <canvas ref="trafficChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Top Posts Chart -->
                <div class="card">
                    <div class="card-content">
                        <div style="height: 400px;">
                            <canvas ref="postsChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Traffic Sources Table -->
                <div v-if="trafficSources.length > 0" class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold">트래픽 소스 상세</h2>
                    </div>
                    <div class="card-content">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>소스</th>
                                    <th>매체</th>
                                    <th>세션</th>
                                    <th>사용자</th>
                                    <th>페이지뷰</th>
                                    <th>비율</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="source in trafficSources" :key="source.source + source.medium">
                                    <td class="font-medium">{{ source.source }}</td>
                                    <td>
                                        <span class="badge badge-info text-xs">{{ source.medium }}</span>
                                    </td>
                                    <td>{{ formatNumber(source.sessions) }}</td>
                                    <td>{{ formatNumber(source.users) }}</td>
                                    <td>{{ formatNumber(source.page_views) }}</td>
                                    <td>
                                        {{ ((source.sessions / totalTrafficSessions) * 100).toFixed(1) }}%
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Top Posts Table -->
                <div v-if="topPosts.length > 0" class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold">인기 포스트 상세</h2>
                    </div>
                    <div class="card-content">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>제목</th>
                                    <th>페이지뷰</th>
                                    <th>방문자</th>
                                    <th>평균 체류시간</th>
                                    <th>참여율</th>
                                    <th>이탈률</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(post, idx) in topPosts" :key="idx">
                                    <td>
                                        <div class="font-medium mb-1">{{ post.page_title }}</div>
                                        <div class="text-xs text-gray-600">{{ post.page_path }}</div>
                                    </td>
                                    <td class="font-semibold">{{ formatNumber(post.page_views) }}</td>
                                    <td>{{ formatNumber(post.unique_users) }}</td>
                                    <td>{{ formatDuration(post.avg_time_on_page) }}</td>
                                    <td>
                                        <span :class="{
                                            'text-green-600': post.engagement_rate >= 70,
                                            'text-yellow-600': post.engagement_rate >= 40 && post.engagement_rate < 70,
                                            'text-red-600': post.engagement_rate < 40
                                        }">
                                            {{ post.engagement_rate.toFixed(1) }}%
                                        </span>
                                    </td>
                                    <td>
                                        <span :class="{
                                            'text-green-600': post.bounce_rate < 40,
                                            'text-yellow-600': post.bounce_rate >= 40 && post.bounce_rate < 70,
                                            'text-red-600': post.bounce_rate >= 70
                                        }">
                                            {{ post.bounce_rate.toFixed(1) }}%
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `
};
