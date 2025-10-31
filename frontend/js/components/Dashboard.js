/**
 * Dashboard Component
 * Main overview page showing statistics, recent workflows, and SEO scores
 */

const DashboardComponent = {
    template: `
        <div>
            <!-- Page Header -->
            <div class="mb-6">
                <h2 class="text-3xl font-bold text-gray-900">
                    <i class="fas fa-chart-line mr-2"></i>
                    대시보드
                </h2>
                <p class="mt-1 text-sm text-gray-600">
                    블로그 자동화 시스템 현황을 한눈에 확인하세요
                </p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <i class="fas fa-spinner fa-spin fa-3x text-indigo-600"></i>
                <p class="mt-4 text-gray-600">데이터를 불러오는 중...</p>
            </div>

            <!-- Stats Grid -->
            <div v-else>
                <!-- Statistics Cards -->
                <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
                    <!-- Total Workflows -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-project-diagram text-3xl text-indigo-600"></i>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">
                                            전체 워크플로우
                                        </dt>
                                        <dd class="flex items-baseline">
                                            <div class="text-2xl font-semibold text-gray-900">
                                                {{ stats.total_workflows || 0 }}
                                            </div>
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <span class="font-medium text-green-600">
                                    {{ stats.completed_workflows || 0 }} 완료
                                </span>
                                <span class="text-gray-500 mx-2">•</span>
                                <span class="font-medium text-blue-600">
                                    {{ stats.running_workflows || 0 }} 실행중
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Total Posts -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-file-alt text-3xl text-green-600"></i>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">
                                            생성된 포스트
                                        </dt>
                                        <dd class="flex items-baseline">
                                            <div class="text-2xl font-semibold text-gray-900">
                                                {{ stats.total_posts || 0 }}
                                            </div>
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <span class="font-medium text-green-600">
                                    {{ stats.published_posts || 0 }} 발행됨
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Average SEO Score -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-search text-3xl text-blue-600"></i>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">
                                            평균 SEO 점수
                                        </dt>
                                        <dd class="flex items-baseline">
                                            <div class="text-2xl font-semibold text-gray-900">
                                                {{ seoStats.average_score?.toFixed(1) || 0 }}
                                            </div>
                                            <div class="ml-2 text-sm text-gray-500">/ 100</div>
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <span class="text-gray-600">
                                    {{ seoStats.total_analyzed || 0 }}개 분석됨
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Success Rate -->
                    <div class="bg-white overflow-hidden shadow rounded-lg">
                        <div class="p-5">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-check-circle text-3xl text-yellow-600"></i>
                                </div>
                                <div class="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt class="text-sm font-medium text-gray-500 truncate">
                                            성공률
                                        </dt>
                                        <dd class="flex items-baseline">
                                            <div class="text-2xl font-semibold text-gray-900">
                                                {{ getSuccessRate() }}%
                                            </div>
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                        <div class="bg-gray-50 px-5 py-3">
                            <div class="text-sm">
                                <span class="text-gray-600">
                                    지난 30일 기준
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts and Recent Activity -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <!-- SEO Score Distribution Chart -->
                    <div class="bg-white shadow rounded-lg p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">
                            <i class="fas fa-chart-pie mr-2"></i>
                            SEO 점수 분포
                        </h3>
                        <div class="chart-container">
                            <canvas ref="seoChart"></canvas>
                        </div>
                    </div>

                    <!-- Recent Workflows -->
                    <div class="bg-white shadow rounded-lg p-6">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium text-gray-900">
                                <i class="fas fa-clock mr-2"></i>
                                최근 워크플로우
                            </h3>
                            <button @click="$emit('start-workflow')"
                                    class="text-sm text-indigo-600 hover:text-indigo-800">
                                새로 시작 <i class="fas fa-arrow-right ml-1"></i>
                            </button>
                        </div>

                        <div v-if="workflows.length === 0" class="empty-state py-8">
                            <i class="fas fa-inbox"></i>
                            <h3>워크플로우가 없습니다</h3>
                            <p>새 워크플로우를 시작해보세요</p>
                        </div>

                        <div v-else class="space-y-3">
                            <div v-for="workflow in workflows.slice(0, 5)"
                                 :key="workflow.id"
                                 class="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition">
                                <div class="flex items-center justify-between">
                                    <div class="flex-1">
                                        <div class="flex items-center">
                                            <span :class="'badge badge-' + workflow.status">
                                                {{ getStatusLabel(workflow.status) }}
                                            </span>
                                            <span class="ml-2 text-sm text-gray-600">
                                                워크플로우 #{{ workflow.id }}
                                            </span>
                                        </div>
                                        <div class="mt-2">
                                            <div class="progress-bar">
                                                <div class="progress-bar-fill"
                                                     :style="{width: workflow.progress_percentage + '%'}"></div>
                                            </div>
                                            <div class="mt-1 text-xs text-gray-500">
                                                {{ workflow.progress_percentage }}% 완료
                                            </div>
                                        </div>
                                    </div>
                                    <div class="ml-4 text-right">
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ workflow.statistics?.posts_created || 0 }} 포스트
                                        </div>
                                        <div class="text-xs text-gray-500">
                                            {{ formatDate(workflow.created_at) }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Top and Bottom Performers -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Top Performers -->
                    <div class="bg-white shadow rounded-lg p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">
                            <i class="fas fa-trophy mr-2 text-yellow-500"></i>
                            높은 SEO 점수
                        </h3>

                        <div v-if="seoStats.top_performers?.length === 0" class="empty-state py-8">
                            <i class="fas fa-chart-line"></i>
                            <p>SEO 분석 데이터가 없습니다</p>
                        </div>

                        <div v-else class="space-y-3">
                            <div v-for="item in seoStats.top_performers"
                                 :key="item.post_id"
                                 class="flex items-center justify-between border-b pb-3">
                                <div class="flex items-center">
                                    <div :class="'grade-badge grade-' + item.grade.toLowerCase().replace('+', '-plus')">
                                        {{ item.grade }}
                                    </div>
                                    <div class="ml-4">
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ item.keyword }}
                                        </div>
                                        <div class="text-xs text-gray-500">
                                            포스트 #{{ item.post_id }}
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-lg font-semibold text-green-600">
                                        {{ item.score }}
                                    </div>
                                    <div class="text-xs text-gray-500">
                                        점
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Needs Improvement -->
                    <div class="bg-white shadow rounded-lg p-6">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">
                            <i class="fas fa-exclamation-triangle mr-2 text-red-500"></i>
                            개선 필요
                        </h3>

                        <div v-if="seoStats.needs_improvement?.length === 0" class="empty-state py-8">
                            <i class="fas fa-check-circle"></i>
                            <p>모든 포스트가 양호합니다!</p>
                        </div>

                        <div v-else class="space-y-3">
                            <div v-for="item in seoStats.needs_improvement"
                                 :key="item.post_id"
                                 class="flex items-center justify-between border-b pb-3">
                                <div class="flex items-center">
                                    <div :class="'grade-badge grade-' + item.grade.toLowerCase().replace('+', '-plus')">
                                        {{ item.grade }}
                                    </div>
                                    <div class="ml-4">
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ item.keyword }}
                                        </div>
                                        <div class="text-xs text-gray-500">
                                            {{ item.issue_count }}개 이슈
                                        </div>
                                    </div>
                                </div>
                                <div class="text-right">
                                    <div class="text-lg font-semibold text-red-600">
                                        {{ item.score }}
                                    </div>
                                    <div class="text-xs text-gray-500">
                                        점
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Quick Actions -->
                <div class="mt-8 bg-indigo-50 rounded-lg p-6">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">
                        <i class="fas fa-bolt mr-2"></i>
                        빠른 작업
                    </h3>
                    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <button @click="$emit('start-workflow')"
                                class="flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                            <i class="fas fa-rocket mr-2"></i>
                            새 워크플로우 시작
                        </button>
                        <button @click="navigateTo('workflows')"
                                class="flex items-center justify-center px-6 py-3 border border-indigo-600 text-base font-medium rounded-md text-indigo-600 bg-white hover:bg-indigo-50">
                            <i class="fas fa-list mr-2"></i>
                            워크플로우 관리
                        </button>
                        <button @click="navigateTo('seo')"
                                class="flex items-center justify-center px-6 py-3 border border-indigo-600 text-base font-medium rounded-md text-indigo-600 bg-white hover:bg-indigo-50">
                            <i class="fas fa-chart-bar mr-2"></i>
                            SEO 분석 보기
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,

    props: {
        stats: Object,
        workflows: Array,
        seoStats: Object,
        loading: Boolean,
    },

    emits: ['start-workflow'],

    data() {
        return {
            chart: null,
        };
    },

    mounted() {
        this.initChart();
    },

    watch: {
        seoStats: {
            deep: true,
            handler() {
                this.updateChart();
            }
        }
    },

    methods: {
        initChart() {
            if (!this.$refs.seoChart) return;

            const ctx = this.$refs.seoChart.getContext('2d');
            this.chart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#10b981', // Green for A+, A
                            '#3b82f6', // Blue for B+, B
                            '#f59e0b', // Yellow for C+, C
                            '#ef4444', // Red for D, F
                        ],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });

            this.updateChart();
        },

        updateChart() {
            if (!this.chart || !this.seoStats.grade_distribution) return;

            const distribution = this.seoStats.grade_distribution;
            const labels = Object.keys(distribution);
            const data = Object.values(distribution);

            this.chart.data.labels = labels;
            this.chart.data.datasets[0].data = data;
            this.chart.update();
        },

        getSuccessRate() {
            const total = this.stats.total_workflows || 1;
            const completed = this.stats.completed_workflows || 0;
            return Math.round((completed / total) * 100);
        },

        getStatusLabel(status) {
            const labels = {
                'pending': '대기중',
                'running': '실행중',
                'completed': '완료',
                'failed': '실패',
                'cancelled': '취소됨',
            };
            return labels[status] || status;
        },

        formatDate(dateString) {
            return api.formatDate(dateString);
        },

        navigateTo(page) {
            this.$emit('navigate', page);
        },
    },
};

// Register component
app.component('dashboard-component', DashboardComponent);
