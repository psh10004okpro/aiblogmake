/**
 * Workflows Component
 * Workflow management UI with real-time progress tracking
 */

const WorkflowsComponent = {
    template: `
        <div>
            <!-- Page Header -->
            <div class="mb-6 flex items-center justify-between">
                <div>
                    <h2 class="text-3xl font-bold text-gray-900">
                        <i class="fas fa-project-diagram mr-2"></i>
                        워크플로우 관리
                    </h2>
                    <p class="mt-1 text-sm text-gray-600">
                        자동화 워크플로우를 관리하고 실시간 진행 상황을 확인하세요
                    </p>
                </div>
                <button @click="$emit('start-workflow')"
                        class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    <i class="fas fa-plus mr-2"></i>
                    새 워크플로우
                </button>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <i class="fas fa-spinner fa-spin fa-3x text-indigo-600"></i>
                <p class="mt-4 text-gray-600">워크플로우를 불러오는 중...</p>
            </div>

            <!-- Filters -->
            <div v-else class="bg-white shadow rounded-lg p-4 mb-6">
                <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">상태</label>
                        <select v-model="filters.status"
                                @change="applyFilters"
                                class="w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            <option value="">전체</option>
                            <option value="pending">대기중</option>
                            <option value="running">실행중</option>
                            <option value="completed">완료</option>
                            <option value="failed">실패</option>
                            <option value="cancelled">취소됨</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">타입</label>
                        <select v-model="filters.workflow_type"
                                @change="applyFilters"
                                class="w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            <option value="">전체</option>
                            <option value="one_click">원클릭</option>
                            <option value="scheduled">스케줄</option>
                            <option value="manual">수동</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">페이지 크기</label>
                        <select v-model.number="filters.page_size"
                                @change="applyFilters"
                                class="w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                            <option :value="10">10개</option>
                            <option :value="20">20개</option>
                            <option :value="50">50개</option>
                        </select>
                    </div>

                    <div class="flex items-end">
                        <button @click="resetFilters"
                                class="w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                            <i class="fas fa-undo mr-2"></i>
                            초기화
                        </button>
                    </div>
                </div>
            </div>

            <!-- Workflows List -->
            <div v-if="!loading">
                <!-- Empty State -->
                <div v-if="filteredWorkflows.length === 0" class="bg-white shadow rounded-lg">
                    <div class="empty-state">
                        <i class="fas fa-folder-open"></i>
                        <h3>워크플로우가 없습니다</h3>
                        <p>필터를 변경하거나 새 워크플로우를 시작해보세요</p>
                        <button @click="$emit('start-workflow')"
                                class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
                            <i class="fas fa-plus mr-2"></i>
                            새 워크플로우 시작
                        </button>
                    </div>
                </div>

                <!-- Workflow Cards -->
                <div v-else class="space-y-4">
                    <div v-for="workflow in filteredWorkflows"
                         :key="workflow.id"
                         class="bg-white shadow rounded-lg overflow-hidden card-hover">
                        <!-- Header -->
                        <div class="px-6 py-4 border-b border-gray-200">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <h3 class="text-lg font-medium text-gray-900">
                                        워크플로우 #{{ workflow.id }}
                                    </h3>
                                    <span :class="'ml-3 badge badge-' + workflow.status">
                                        {{ getStatusLabel(workflow.status) }}
                                    </span>
                                    <span v-if="workflow.status === 'running'" class="ml-2">
                                        <i class="fas fa-circle text-blue-500 pulse" style="font-size: 0.5rem;"></i>
                                    </span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <button @click="toggleDetails(workflow.id)"
                                            class="text-gray-400 hover:text-gray-600">
                                        <i :class="'fas fa-chevron-' + (expandedWorkflows.includes(workflow.id) ? 'up' : 'down')"></i>
                                    </button>
                                    <button v-if="workflow.status === 'running' || workflow.status === 'pending'"
                                            @click="cancelWorkflow(workflow.id)"
                                            class="text-red-600 hover:text-red-800">
                                        <i class="fas fa-stop-circle"></i>
                                    </button>
                                    <button v-if="workflow.status === 'completed' || workflow.status === 'failed'"
                                            @click="deleteWorkflow(workflow.id)"
                                            class="text-gray-400 hover:text-gray-600">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Body -->
                        <div class="px-6 py-4">
                            <!-- Progress Bar -->
                            <div class="mb-4">
                                <div class="flex items-center justify-between mb-1">
                                    <span class="text-sm font-medium text-gray-700">
                                        {{ workflow.current_step || '대기중' }}
                                    </span>
                                    <span class="text-sm font-medium text-gray-900">
                                        {{ workflow.progress_percentage }}%
                                    </span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-bar-fill"
                                         :style="{width: workflow.progress_percentage + '%'}"></div>
                                </div>
                            </div>

                            <!-- Stats Grid -->
                            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                                <div>
                                    <div class="text-xs text-gray-500">키워드 리서치</div>
                                    <div class="text-lg font-semibold text-gray-900">
                                        {{ workflow.statistics?.keywords_researched || 0 }}
                                    </div>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-500">생성됨</div>
                                    <div class="text-lg font-semibold text-gray-900">
                                        {{ workflow.statistics?.posts_created || 0 }}
                                    </div>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-500">발행됨</div>
                                    <div class="text-lg font-semibold text-gray-900">
                                        {{ workflow.statistics?.posts_published || 0 }}
                                    </div>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-500">에러</div>
                                    <div class="text-lg font-semibold"
                                         :class="workflow.statistics?.errors > 0 ? 'text-red-600' : 'text-gray-900'">
                                        {{ workflow.statistics?.errors || 0 }}
                                    </div>
                                </div>
                            </div>

                            <!-- Details (Expandable) -->
                            <div v-if="expandedWorkflows.includes(workflow.id)"
                                 class="border-t border-gray-200 pt-4 mt-4">
                                <!-- Workflow Info -->
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                                    <div>
                                        <div class="text-sm text-gray-500">타입</div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ getWorkflowTypeLabel(workflow.workflow_type) }}
                                        </div>
                                    </div>
                                    <div>
                                        <div class="text-sm text-gray-500">생성 시간</div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ formatDate(workflow.created_at) }}
                                        </div>
                                    </div>
                                    <div>
                                        <div class="text-sm text-gray-500">시작 시간</div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ formatDate(workflow.started_at) }}
                                        </div>
                                    </div>
                                    <div v-if="workflow.completed_at">
                                        <div class="text-sm text-gray-500">완료 시간</div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ formatDate(workflow.completed_at) }}
                                        </div>
                                    </div>
                                    <div v-if="workflow.duration_seconds">
                                        <div class="text-sm text-gray-500">소요 시간</div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {{ formatDuration(workflow.duration_seconds) }}
                                        </div>
                                    </div>
                                </div>

                                <!-- Steps Timeline -->
                                <div v-if="workflow.steps && Object.keys(workflow.steps).length > 0"
                                     class="mt-4">
                                    <h4 class="text-sm font-medium text-gray-900 mb-3">실행 단계</h4>
                                    <div class="timeline">
                                        <div v-for="(step, stepName) in workflow.steps"
                                             :key="stepName"
                                             :class="'timeline-item ' + step.status">
                                            <div class="bg-white rounded-lg p-3 border">
                                                <div class="flex items-center justify-between">
                                                    <div>
                                                        <div class="text-sm font-medium text-gray-900">
                                                            {{ formatStepName(stepName) }}
                                                        </div>
                                                        <div class="text-xs text-gray-500">
                                                            {{ getStepStatusLabel(step.status) }}
                                                        </div>
                                                    </div>
                                                    <div v-if="step.status === 'completed'" class="text-green-500">
                                                        <i class="fas fa-check-circle"></i>
                                                    </div>
                                                    <div v-else-if="step.status === 'failed'" class="text-red-500">
                                                        <i class="fas fa-times-circle"></i>
                                                    </div>
                                                    <div v-else-if="step.status === 'running'" class="text-blue-500">
                                                        <i class="fas fa-spinner fa-spin"></i>
                                                    </div>
                                                </div>
                                                <div v-if="step.error" class="mt-2 text-xs text-red-600">
                                                    {{ step.error }}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Errors -->
                                <div v-if="workflow.errors && workflow.errors.length > 0"
                                     class="mt-4">
                                    <h4 class="text-sm font-medium text-red-900 mb-2">에러</h4>
                                    <div class="space-y-2">
                                        <div v-for="(error, index) in workflow.errors"
                                             :key="index"
                                             class="bg-red-50 border border-red-200 rounded-lg p-3">
                                            <div class="text-sm text-red-800">
                                                {{ error.error || error.message || JSON.stringify(error) }}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Pagination -->
                <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
                    <div class="text-sm text-gray-700">
                        {{ ((filters.page - 1) * filters.page_size) + 1 }}-{{ Math.min(filters.page * filters.page_size, totalWorkflows) }}
                        / {{ totalWorkflows }}개
                    </div>
                    <div class="flex space-x-2">
                        <button @click="previousPage"
                                :disabled="filters.page === 1"
                                class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                        <span class="px-4 py-2 text-sm text-gray-700">
                            페이지 {{ filters.page }} / {{ totalPages }}
                        </span>
                        <button @click="nextPage"
                                :disabled="filters.page === totalPages"
                                class="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                            <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,

    props: {
        workflows: Array,
        loading: Boolean,
    },

    emits: ['start-workflow', 'view-workflow', 'cancel-workflow'],

    data() {
        return {
            filters: {
                status: '',
                workflow_type: '',
                page: 1,
                page_size: 20,
            },
            expandedWorkflows: [],
            pollingIntervals: {},
        };
    },

    computed: {
        filteredWorkflows() {
            return this.workflows || [];
        },

        totalWorkflows() {
            return this.filteredWorkflows.length;
        },

        totalPages() {
            return Math.ceil(this.totalWorkflows / this.filters.page_size);
        },
    },

    mounted() {
        this.startPolling();
    },

    beforeUnmount() {
        this.stopPolling();
    },

    methods: {
        applyFilters() {
            this.$emit('filter-change', this.filters);
        },

        resetFilters() {
            this.filters = {
                status: '',
                workflow_type: '',
                page: 1,
                page_size: 20,
            };
            this.applyFilters();
        },

        previousPage() {
            if (this.filters.page > 1) {
                this.filters.page--;
                this.applyFilters();
            }
        },

        nextPage() {
            if (this.filters.page < this.totalPages) {
                this.filters.page++;
                this.applyFilters();
            }
        },

        toggleDetails(workflowId) {
            const index = this.expandedWorkflows.indexOf(workflowId);
            if (index > -1) {
                this.expandedWorkflows.splice(index, 1);
            } else {
                this.expandedWorkflows.push(workflowId);
            }
        },

        async cancelWorkflow(workflowId) {
            if (confirm('이 워크플로우를 취소하시겠습니까?')) {
                this.$emit('cancel-workflow', workflowId);
            }
        },

        async deleteWorkflow(workflowId) {
            if (confirm('이 워크플로우를 삭제하시겠습니까?')) {
                this.$emit('delete-workflow', workflowId);
            }
        },

        startPolling() {
            // Poll running workflows every 3 seconds
            this.pollingInterval = setInterval(() => {
                const runningWorkflows = this.workflows.filter(
                    w => w.status === 'running' || w.status === 'pending'
                );
                if (runningWorkflows.length > 0) {
                    this.$emit('poll-workflows');
                }
            }, 3000);
        },

        stopPolling() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
            }
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

        getWorkflowTypeLabel(type) {
            const labels = {
                'one_click': '원클릭 자동화',
                'scheduled': '스케줄된 작업',
                'manual': '수동 실행',
            };
            return labels[type] || type;
        },

        getStepStatusLabel(status) {
            const labels = {
                'pending': '대기중',
                'running': '실행중',
                'completed': '완료',
                'failed': '실패',
            };
            return labels[status] || status;
        },

        formatStepName(stepName) {
            // Convert step_name to readable format
            return stepName
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
        },

        formatDate(dateString) {
            return api.formatDate(dateString);
        },

        formatDuration(seconds) {
            return api.formatDuration(seconds);
        },
    },
};

// Register component
app.component('workflows-component', WorkflowsComponent);
