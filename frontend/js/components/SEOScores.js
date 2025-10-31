/**
 * SEO Scores Component
 *
 * Displays and manages SEO analysis results with filtering and visualization.
 */
export default {
    name: 'SEOScores',

    data() {
        return {
            scores: [],
            stats: null,
            loading: false,
            error: null,

            // Filters
            filters: {
                minScore: null,
                maxScore: null,
                grade: null,
                search: '',
                limit: 20,
                offset: 0
            },

            // UI state
            selectedScore: null,
            showDetailModal: false,
            analyzingPostId: null,

            // Chart
            chart: null,

            // Pagination
            totalCount: 0,
            currentPage: 1
        };
    },

    computed: {
        filteredScores() {
            let filtered = [...this.scores];

            // Search filter
            if (this.filters.search) {
                const search = this.filters.search.toLowerCase();
                filtered = filtered.filter(score =>
                    score.target_keyword?.toLowerCase().includes(search) ||
                    score.post_id?.toString().includes(search)
                );
            }

            return filtered;
        },

        totalPages() {
            return Math.ceil(this.totalCount / this.filters.limit);
        },

        gradeOptions() {
            return ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F'];
        }
    },

    async mounted() {
        await this.loadScores();
        await this.loadStats();
        this.initChart();
    },

    beforeUnmount() {
        if (this.chart) {
            this.chart.destroy();
        }
    },

    methods: {
        async loadScores() {
            this.loading = true;
            this.error = null;

            try {
                const params = {};

                if (this.filters.minScore !== null && this.filters.minScore !== '') {
                    params.min_score = this.filters.minScore;
                }

                if (this.filters.maxScore !== null && this.filters.maxScore !== '') {
                    params.max_score = this.filters.maxScore;
                }

                if (this.filters.grade) {
                    params.grade = this.filters.grade;
                }

                params.limit = this.filters.limit;
                params.offset = this.filters.offset;

                const response = await api.seo.list(params);
                this.scores = response.data;

                // Update total count (approximate from response length)
                if (response.data.length < this.filters.limit) {
                    this.totalCount = this.filters.offset + response.data.length;
                } else {
                    this.totalCount = this.filters.offset + response.data.length + 1;
                }

            } catch (error) {
                console.error('Failed to load SEO scores:', error);
                this.error = 'SEO 점수를 불러오는데 실패했습니다.';
                this.$emit('show-toast', {
                    message: 'SEO 점수 로드 실패',
                    type: 'error'
                });
            } finally {
                this.loading = false;
            }
        },

        async loadStats() {
            try {
                const response = await api.seo.getStats();
                this.stats = response.data;

                // Update chart with stats
                if (this.chart && this.stats.grade_distribution) {
                    this.updateChart(this.stats.grade_distribution);
                }
            } catch (error) {
                console.error('Failed to load SEO stats:', error);
            }
        },

        initChart() {
            const canvas = this.$refs.gradeChart;
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

            this.chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: [],
                    datasets: [{
                        label: '포스트 수',
                        data: [],
                        backgroundColor: [
                            'rgba(16, 185, 129, 0.8)',  // A+
                            'rgba(34, 197, 94, 0.8)',   // A
                            'rgba(132, 204, 22, 0.8)',  // B+
                            'rgba(234, 179, 8, 0.8)',   // B
                            'rgba(249, 115, 22, 0.8)',  // C+
                            'rgba(239, 68, 68, 0.8)',   // C
                            'rgba(220, 38, 38, 0.8)',   // D
                            'rgba(127, 29, 29, 0.8)'    // F
                        ],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: '등급별 분포',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        },

        updateChart(gradeDistribution) {
            if (!this.chart) return;

            const grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F'];
            const data = grades.map(grade => gradeDistribution[grade] || 0);

            this.chart.data.labels = grades;
            this.chart.data.datasets[0].data = data;
            this.chart.update();
        },

        async analyzePost() {
            const postId = prompt('분석할 포스트 ID를 입력하세요:');

            if (!postId) return;

            this.analyzingPostId = parseInt(postId);

            try {
                this.$emit('show-toast', {
                    message: `포스트 #${postId} 분석 중...`,
                    type: 'info'
                });

                const response = await api.seo.analyzePost(postId, true);

                this.$emit('show-toast', {
                    message: `분석 완료! 점수: ${response.data.overall_score.toFixed(1)} (${response.data.grade})`,
                    type: 'success'
                });

                // Reload scores to include new analysis
                await this.loadScores();
                await this.loadStats();

            } catch (error) {
                console.error('Failed to analyze post:', error);
                this.$emit('show-toast', {
                    message: error.response?.data?.detail || 'SEO 분석 실패',
                    type: 'error'
                });
            } finally {
                this.analyzingPostId = null;
            }
        },

        async viewDetails(score) {
            this.selectedScore = score;
            this.showDetailModal = true;
        },

        async deleteScore(postId) {
            if (!confirm(`포스트 #${postId}의 SEO 점수를 삭제하시겠습니까?`)) {
                return;
            }

            try {
                await api.seo.deleteScore(postId);

                this.$emit('show-toast', {
                    message: 'SEO 점수가 삭제되었습니다.',
                    type: 'success'
                });

                // Reload scores
                await this.loadScores();
                await this.loadStats();

            } catch (error) {
                console.error('Failed to delete score:', error);
                this.$emit('show-toast', {
                    message: 'SEO 점수 삭제 실패',
                    type: 'error'
                });
            }
        },

        async applyFilters() {
            this.filters.offset = 0;
            this.currentPage = 1;
            await this.loadScores();
        },

        async clearFilters() {
            this.filters.minScore = null;
            this.filters.maxScore = null;
            this.filters.grade = null;
            this.filters.search = '';
            this.filters.offset = 0;
            this.currentPage = 1;
            await this.loadScores();
        },

        async changePage(page) {
            this.currentPage = page;
            this.filters.offset = (page - 1) * this.filters.limit;
            await this.loadScores();
        },

        async prevPage() {
            if (this.currentPage > 1) {
                await this.changePage(this.currentPage - 1);
            }
        },

        async nextPage() {
            if (this.currentPage < this.totalPages) {
                await this.changePage(this.currentPage + 1);
            }
        },

        closeDetailModal() {
            this.showDetailModal = false;
            this.selectedScore = null;
        },

        getComponentScoreColor(score) {
            if (score >= 90) return 'text-green-600';
            if (score >= 80) return 'text-lime-600';
            if (score >= 70) return 'text-yellow-600';
            if (score >= 60) return 'text-orange-600';
            return 'text-red-600';
        },

        getIssueIcon(severity) {
            const icons = {
                critical: '⛔',
                high: '🔴',
                medium: '🟡',
                low: '🟢',
                info: 'ℹ️'
            };
            return icons[severity] || 'ℹ️';
        }
    },

    template: `
        <div class="seo-scores-container">
            <!-- Stats Cards -->
            <div v-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="stat-card">
                    <div class="stat-icon bg-blue-100">
                        <i class="fas fa-chart-line text-blue-600"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">분석된 포스트</div>
                        <div class="stat-value">{{ stats.total_analyzed }}</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon bg-green-100">
                        <i class="fas fa-star text-green-600"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">평균 점수</div>
                        <div class="stat-value">{{ stats.average_score.toFixed(1) }}</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon bg-purple-100">
                        <i class="fas fa-trophy text-purple-600"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-label">최고 등급</div>
                        <div class="stat-value">
                            <span v-if="stats.top_performers.length > 0"
                                  :class="api.getGradeColor(stats.top_performers[0].grade)"
                                  class="grade-badge">
                                {{ stats.top_performers[0].grade }}
                            </span>
                            <span v-else>-</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Grade Distribution Chart -->
            <div class="card mb-8">
                <div class="card-header">
                    <h2 class="text-xl font-bold">등급별 분포</h2>
                </div>
                <div class="card-content">
                    <div style="height: 300px;">
                        <canvas ref="gradeChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Filters -->
            <div class="card mb-6">
                <div class="card-header">
                    <h2 class="text-xl font-bold">필터</h2>
                    <button @click="analyzePost" class="btn btn-primary">
                        <i class="fas fa-search"></i>
                        포스트 분석
                    </button>
                </div>
                <div class="card-content">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                최소 점수
                            </label>
                            <input
                                v-model.number="filters.minScore"
                                type="number"
                                min="0"
                                max="100"
                                placeholder="0"
                                class="input"
                            />
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                최대 점수
                            </label>
                            <input
                                v-model.number="filters.maxScore"
                                type="number"
                                min="0"
                                max="100"
                                placeholder="100"
                                class="input"
                            />
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                등급
                            </label>
                            <select v-model="filters.grade" class="input">
                                <option :value="null">전체</option>
                                <option v-for="grade in gradeOptions" :key="grade" :value="grade">
                                    {{ grade }}
                                </option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                검색
                            </label>
                            <input
                                v-model="filters.search"
                                type="text"
                                placeholder="키워드 검색..."
                                class="input"
                            />
                        </div>
                    </div>

                    <div class="flex gap-4 mt-4">
                        <button @click="applyFilters" class="btn btn-primary">
                            <i class="fas fa-filter"></i>
                            필터 적용
                        </button>
                        <button @click="clearFilters" class="btn btn-secondary">
                            <i class="fas fa-times"></i>
                            초기화
                        </button>
                    </div>
                </div>
            </div>

            <!-- Error Message -->
            <div v-if="error" class="alert alert-error mb-6">
                <i class="fas fa-exclamation-circle"></i>
                {{ error }}
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">SEO 점수 로딩 중...</p>
            </div>

            <!-- Scores List -->
            <div v-else-if="filteredScores.length > 0" class="space-y-4">
                <div
                    v-for="score in filteredScores"
                    :key="score.id"
                    class="card score-card"
                >
                    <div class="card-content">
                        <div class="flex items-start justify-between mb-4">
                            <div class="flex-1">
                                <div class="flex items-center gap-3 mb-2">
                                    <span :class="api.getGradeColor(score.grade)" class="grade-badge text-2xl font-bold">
                                        {{ score.grade }}
                                    </span>
                                    <div>
                                        <h3 class="text-lg font-semibold">
                                            포스트 #{{ score.post_id }}
                                        </h3>
                                        <p class="text-sm text-gray-600">
                                            키워드: {{ score.target_keyword || '없음' }}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div class="text-right">
                                <div class="text-3xl font-bold text-gray-900">
                                    {{ score.overall_score.toFixed(1) }}
                                </div>
                                <div class="text-sm text-gray-500">
                                    {{ api.formatDate(score.analyzed_at) }}
                                </div>
                            </div>
                        </div>

                        <!-- Component Scores -->
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">키워드 밀도</div>
                                <div :class="getComponentScoreColor(score.keyword_density_score)" class="font-semibold">
                                    {{ score.keyword_density_score.toFixed(1) }}
                                </div>
                            </div>

                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">제목 최적화</div>
                                <div :class="getComponentScoreColor(score.title_optimization_score)" class="font-semibold">
                                    {{ score.title_optimization_score.toFixed(1) }}
                                </div>
                            </div>

                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">메타 태그</div>
                                <div :class="getComponentScoreColor(score.meta_tags_score)" class="font-semibold">
                                    {{ score.meta_tags_score.toFixed(1) }}
                                </div>
                            </div>

                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">가독성</div>
                                <div :class="getComponentScoreColor(score.readability_score)" class="font-semibold">
                                    {{ score.readability_score.toFixed(1) }}
                                </div>
                            </div>

                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">내부 링크</div>
                                <div :class="getComponentScoreColor(score.internal_links_score)" class="font-semibold">
                                    {{ score.internal_links_score.toFixed(1) }}
                                </div>
                            </div>

                            <div class="score-component">
                                <div class="text-sm text-gray-600 mb-1">이미지 Alt</div>
                                <div :class="getComponentScoreColor(score.image_alt_score)" class="font-semibold">
                                    {{ score.image_alt_score.toFixed(1) }}
                                </div>
                            </div>
                        </div>

                        <!-- Issues Summary -->
                        <div v-if="score.issues && score.issues.length > 0" class="mb-4">
                            <div class="text-sm font-medium text-gray-700 mb-2">
                                이슈 ({{ score.issues.length }}개)
                            </div>
                            <div class="flex flex-wrap gap-2">
                                <span
                                    v-for="(issue, idx) in score.issues.slice(0, 3)"
                                    :key="idx"
                                    class="badge badge-warning text-xs"
                                >
                                    {{ getIssueIcon(issue.severity) }} {{ issue.category }}
                                </span>
                                <span v-if="score.issues.length > 3" class="text-sm text-gray-500">
                                    +{{ score.issues.length - 3 }} more
                                </span>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="flex gap-2">
                            <button @click="viewDetails(score)" class="btn btn-sm btn-primary">
                                <i class="fas fa-eye"></i>
                                상세보기
                            </button>
                            <button @click="deleteScore(score.post_id)" class="btn btn-sm btn-danger">
                                <i class="fas fa-trash"></i>
                                삭제
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Empty State -->
            <div v-else class="text-center py-12">
                <i class="fas fa-chart-bar text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-600 mb-4">SEO 점수가 없습니다.</p>
                <button @click="analyzePost" class="btn btn-primary">
                    <i class="fas fa-search"></i>
                    포스트 분석하기
                </button>
            </div>

            <!-- Pagination -->
            <div v-if="filteredScores.length > 0" class="flex items-center justify-between mt-6">
                <div class="text-sm text-gray-600">
                    페이지 {{ currentPage }} / {{ totalPages }}
                </div>

                <div class="flex gap-2">
                    <button
                        @click="prevPage"
                        :disabled="currentPage === 1"
                        class="btn btn-sm btn-secondary"
                        :class="{ 'opacity-50 cursor-not-allowed': currentPage === 1 }"
                    >
                        <i class="fas fa-chevron-left"></i>
                        이전
                    </button>

                    <button
                        @click="nextPage"
                        :disabled="currentPage >= totalPages"
                        class="btn btn-sm btn-secondary"
                        :class="{ 'opacity-50 cursor-not-allowed': currentPage >= totalPages }"
                    >
                        다음
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>

            <!-- Detail Modal -->
            <div v-if="showDetailModal && selectedScore" class="modal-overlay" @click="closeDetailModal">
                <div class="modal-content" @click.stop style="max-width: 900px;">
                    <div class="modal-header">
                        <h2 class="text-2xl font-bold">SEO 분석 상세</h2>
                        <button @click="closeDetailModal" class="text-gray-400 hover:text-gray-600">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>

                    <div class="modal-body" style="max-height: 600px; overflow-y: auto;">
                        <!-- Score Overview -->
                        <div class="mb-6 text-center">
                            <div class="mb-2">
                                <span :class="api.getGradeColor(selectedScore.grade)" class="grade-badge text-4xl font-bold">
                                    {{ selectedScore.grade }}
                                </span>
                            </div>
                            <div class="text-5xl font-bold text-gray-900 mb-2">
                                {{ selectedScore.overall_score.toFixed(1) }}
                            </div>
                            <div class="text-gray-600">
                                포스트 #{{ selectedScore.post_id }} - {{ selectedScore.target_keyword }}
                            </div>
                        </div>

                        <!-- Component Scores Detail -->
                        <div class="mb-6">
                            <h3 class="text-lg font-bold mb-4">세부 점수</h3>
                            <div class="space-y-3">
                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">키워드 밀도</span>
                                        <span :class="getComponentScoreColor(selectedScore.keyword_density_score)" class="font-semibold">
                                            {{ selectedScore.keyword_density_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.keyword_density_score + '%' }"
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">제목 최적화</span>
                                        <span :class="getComponentScoreColor(selectedScore.title_optimization_score)" class="font-semibold">
                                            {{ selectedScore.title_optimization_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.title_optimization_score + '%' }"
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">메타 태그</span>
                                        <span :class="getComponentScoreColor(selectedScore.meta_tags_score)" class="font-semibold">
                                            {{ selectedScore.meta_tags_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.meta_tags_score + '%' }"
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">가독성</span>
                                        <span :class="getComponentScoreColor(selectedScore.readability_score)" class="font-semibold">
                                            {{ selectedScore.readability_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.readability_score + '%' }"
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">내부 링크</span>
                                        <span :class="getComponentScoreColor(selectedScore.internal_links_score)" class="font-semibold">
                                            {{ selectedScore.internal_links_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.internal_links_score + '%' }"
                                        ></div>
                                    </div>
                                </div>

                                <div>
                                    <div class="flex justify-between mb-1">
                                        <span class="text-sm font-medium">이미지 Alt</span>
                                        <span :class="getComponentScoreColor(selectedScore.image_alt_score)" class="font-semibold">
                                            {{ selectedScore.image_alt_score.toFixed(1) }}
                                        </span>
                                    </div>
                                    <div class="progress-bar">
                                        <div
                                            class="progress-fill"
                                            :style="{ width: selectedScore.image_alt_score + '%' }"
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Issues -->
                        <div v-if="selectedScore.issues && selectedScore.issues.length > 0" class="mb-6">
                            <h3 class="text-lg font-bold mb-4">발견된 이슈</h3>
                            <div class="space-y-2">
                                <div
                                    v-for="(issue, idx) in selectedScore.issues"
                                    :key="idx"
                                    class="p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
                                >
                                    <div class="flex items-start gap-2">
                                        <span class="text-lg">{{ getIssueIcon(issue.severity) }}</span>
                                        <div class="flex-1">
                                            <div class="font-semibold text-sm">{{ issue.category }}</div>
                                            <div class="text-sm text-gray-700">{{ issue.message }}</div>
                                        </div>
                                        <span :class="{
                                            'badge-error': issue.severity === 'critical' || issue.severity === 'high',
                                            'badge-warning': issue.severity === 'medium',
                                            'badge-info': issue.severity === 'low' || issue.severity === 'info'
                                        }" class="badge text-xs">
                                            {{ issue.severity }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Suggestions -->
                        <div v-if="selectedScore.suggestions && selectedScore.suggestions.length > 0" class="mb-6">
                            <h3 class="text-lg font-bold mb-4">개선 제안</h3>
                            <ul class="space-y-2">
                                <li
                                    v-for="(suggestion, idx) in selectedScore.suggestions"
                                    :key="idx"
                                    class="flex items-start gap-2 text-sm"
                                >
                                    <i class="fas fa-lightbulb text-yellow-500 mt-1"></i>
                                    <span>{{ suggestion }}</span>
                                </li>
                            </ul>
                        </div>

                        <!-- Metrics -->
                        <div v-if="selectedScore.metrics" class="mb-6">
                            <h3 class="text-lg font-bold mb-4">메트릭</h3>
                            <div class="grid grid-cols-2 gap-4">
                                <div v-for="(value, key) in selectedScore.metrics" :key="key" class="p-3 bg-gray-50 rounded-lg">
                                    <div class="text-xs text-gray-600 mb-1">{{ key }}</div>
                                    <div class="font-semibold">{{ value }}</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button @click="closeDetailModal" class="btn btn-secondary">
                            닫기
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
};
