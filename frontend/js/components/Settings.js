/**
 * Settings Component
 *
 * Manages system configuration and notification settings.
 */
export default {
    name: 'Settings',

    data() {
        return {
            notificationStatus: null,
            loading: false,
            testingNotification: false,
            testResult: null,

            // Test notification form
            testForm: {
                title: 'Test Notification',
                message: 'This is a test notification to verify your configuration.',
                notification_type: 'info',
                priority: 'normal'
            },

            // Notification types and priorities
            notificationTypes: [
                { value: 'info', label: '정보', icon: 'fa-info-circle', color: 'blue' },
                { value: 'success', label: '성공', icon: 'fa-check-circle', color: 'green' },
                { value: 'warning', label: '경고', icon: 'fa-exclamation-triangle', color: 'yellow' },
                { value: 'error', label: '오류', icon: 'fa-times-circle', color: 'red' }
            ],

            priorities: [
                { value: 'low', label: '낮음' },
                { value: 'normal', label: '보통' },
                { value: 'high', label: '높음' },
                { value: 'urgent', label: '긴급' }
            ]
        };
    },

    computed: {
        isNotificationConfigured() {
            return this.notificationStatus &&
                   this.notificationStatus.available &&
                   this.notificationStatus.active_providers &&
                   this.notificationStatus.active_providers.length > 0;
        },

        selectedNotificationType() {
            return this.notificationTypes.find(t => t.value === this.testForm.notification_type);
        }
    },

    async mounted() {
        await this.loadNotificationStatus();
    },

    methods: {
        async loadNotificationStatus() {
            this.loading = true;

            try {
                const response = await api.notifications.getStatus();
                this.notificationStatus = response.data;
            } catch (error) {
                console.error('Failed to load notification status:', error);
                this.$emit('show-toast', {
                    message: '알림 상태 로드 실패',
                    type: 'error'
                });
            } finally {
                this.loading = false;
            }
        },

        async sendTestNotification() {
            if (!this.testForm.title || !this.testForm.message) {
                this.$emit('show-toast', {
                    message: '제목과 메시지를 입력하세요.',
                    type: 'warning'
                });
                return;
            }

            this.testingNotification = true;
            this.testResult = null;

            try {
                const response = await api.notifications.sendTest({
                    title: this.testForm.title,
                    message: this.testForm.message,
                    notification_type: this.testForm.notification_type,
                    priority: this.testForm.priority,
                    metadata: {
                        test: true,
                        timestamp: new Date().toISOString()
                    }
                });

                this.testResult = response.data;

                if (response.data.success) {
                    this.$emit('show-toast', {
                        message: `테스트 알림 전송 성공 (${response.data.providers_succeeded}/${response.data.providers_attempted})`,
                        type: 'success'
                    });
                } else {
                    this.$emit('show-toast', {
                        message: '테스트 알림 전송 실패',
                        type: 'error'
                    });
                }

            } catch (error) {
                console.error('Failed to send test notification:', error);
                this.$emit('show-toast', {
                    message: error.response?.data?.detail || '테스트 알림 전송 실패',
                    type: 'error'
                });
            } finally {
                this.testingNotification = false;
            }
        },

        async testWorkflowCompleteNotification() {
            this.testingNotification = true;

            try {
                const response = await api.notifications.sendTestWorkflowComplete();

                this.$emit('show-toast', {
                    message: '워크플로우 완료 알림 테스트 전송됨',
                    type: 'success'
                });

            } catch (error) {
                console.error('Failed to send test workflow notification:', error);
                this.$emit('show-toast', {
                    message: '테스트 알림 전송 실패',
                    type: 'error'
                });
            } finally {
                this.testingNotification = false;
            }
        },

        async testWorkflowFailedNotification() {
            this.testingNotification = true;

            try {
                const response = await api.notifications.sendTestWorkflowFailed();

                this.$emit('show-toast', {
                    message: '워크플로우 실패 알림 테스트 전송됨',
                    type: 'success'
                });

            } catch (error) {
                console.error('Failed to send test workflow notification:', error);
                this.$emit('show-toast', {
                    message: '테스트 알림 전송 실패',
                    type: 'error'
                });
            } finally {
                this.testingNotification = false;
            }
        },

        getProviderIcon(provider) {
            const icons = {
                'EmailNotificationProvider': 'fa-envelope',
                'SlackNotificationProvider': 'fa-slack',
                'email': 'fa-envelope',
                'slack': 'fa-slack'
            };
            return icons[provider] || 'fa-bell';
        },

        getProviderName(provider) {
            const names = {
                'EmailNotificationProvider': '이메일',
                'SlackNotificationProvider': 'Slack',
                'email': '이메일',
                'slack': 'Slack'
            };
            return names[provider] || provider;
        }
    },

    template: `
        <div class="settings-container">
            <!-- Page Header -->
            <div class="mb-8">
                <h1 class="text-3xl font-bold text-gray-900 mb-2">설정</h1>
                <p class="text-gray-600">시스템 설정 및 알림 관리</p>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-12">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600">설정 로딩 중...</p>
            </div>

            <div v-else class="space-y-6">
                <!-- Notification Status -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold flex items-center gap-2">
                            <i class="fas fa-bell"></i>
                            알림 시스템 상태
                        </h2>
                        <button @click="loadNotificationStatus" class="btn btn-sm btn-secondary">
                            <i class="fas fa-sync-alt"></i>
                            새로고침
                        </button>
                    </div>

                    <div class="card-content">
                        <div v-if="notificationStatus" class="space-y-4">
                            <!-- Overall Status -->
                            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                <div class="flex items-center gap-3">
                                    <div :class="isNotificationConfigured ? 'bg-green-100' : 'bg-red-100'" class="w-12 h-12 rounded-full flex items-center justify-center">
                                        <i :class="isNotificationConfigured ? 'fa-check text-green-600' : 'fa-times text-red-600'" class="fas text-xl"></i>
                                    </div>
                                    <div>
                                        <div class="font-semibold">
                                            {{ isNotificationConfigured ? '알림 시스템 활성' : '알림 시스템 비활성' }}
                                        </div>
                                        <div class="text-sm text-gray-600">
                                            {{ notificationStatus.active_providers ? notificationStatus.active_providers.length : 0 }}개 제공자 활성
                                        </div>
                                    </div>
                                </div>

                                <span v-if="isNotificationConfigured" class="badge badge-success">
                                    <i class="fas fa-check-circle"></i>
                                    정상
                                </span>
                                <span v-else class="badge badge-error">
                                    <i class="fas fa-exclamation-circle"></i>
                                    미설정
                                </span>
                            </div>

                            <!-- Active Providers -->
                            <div v-if="notificationStatus.active_providers && notificationStatus.active_providers.length > 0">
                                <h3 class="font-semibold mb-3">활성 제공자</h3>
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div
                                        v-for="provider in notificationStatus.active_providers"
                                        :key="provider"
                                        class="flex items-center gap-3 p-3 border border-gray-200 rounded-lg"
                                    >
                                        <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                                            <i :class="getProviderIcon(provider)" class="fab text-blue-600"></i>
                                        </div>
                                        <div class="flex-1">
                                            <div class="font-medium">{{ getProviderName(provider) }}</div>
                                            <div class="text-xs text-gray-600">활성화됨</div>
                                        </div>
                                        <i class="fas fa-check-circle text-green-600"></i>
                                    </div>
                                </div>
                            </div>

                            <!-- Configuration Status -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="p-4 border border-gray-200 rounded-lg">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="font-medium">이메일 설정</span>
                                        <span :class="notificationStatus.email_configured ? 'badge-success' : 'badge-error'" class="badge">
                                            {{ notificationStatus.email_configured ? '설정됨' : '미설정' }}
                                        </span>
                                    </div>
                                    <p class="text-sm text-gray-600">
                                        {{ notificationStatus.email_configured
                                            ? 'SMTP 서버가 설정되어 이메일 알림을 보낼 수 있습니다.'
                                            : '.env 파일에서 SMTP 설정을 구성하세요.'
                                        }}
                                    </p>
                                </div>

                                <div class="p-4 border border-gray-200 rounded-lg">
                                    <div class="flex items-center justify-between mb-2">
                                        <span class="font-medium">Slack 설정</span>
                                        <span :class="notificationStatus.slack_configured ? 'badge-success' : 'badge-error'" class="badge">
                                            {{ notificationStatus.slack_configured ? '설정됨' : '미설정' }}
                                        </span>
                                    </div>
                                    <p class="text-sm text-gray-600">
                                        {{ notificationStatus.slack_configured
                                            ? 'Webhook URL이 설정되어 Slack 알림을 보낼 수 있습니다.'
                                            : '.env 파일에서 SLACK_WEBHOOK_URL을 구성하세요.'
                                        }}
                                    </p>
                                </div>
                            </div>

                            <!-- Configuration Guide -->
                            <div v-if="!isNotificationConfigured" class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <h4 class="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    알림 설정 필요
                                </h4>
                                <p class="text-sm text-yellow-800 mb-3">
                                    알림 기능을 사용하려면 .env 파일에서 다음 설정을 구성하세요:
                                </p>
                                <div class="bg-yellow-100 p-3 rounded font-mono text-xs overflow-x-auto">
                                    <pre># 이메일 설정
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFY_EMAILS=admin@yourblog.com

# Slack 설정
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#blog-automation

# 알림 활성화
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_SLACK_NOTIFICATIONS=True</pre>
                                </div>
                                <p class="text-sm text-yellow-800 mt-3">
                                    자세한 설정 방법은 <a href="/docs/NOTIFICATIONS.md" target="_blank" class="underline">알림 시스템 문서</a>를 참조하세요.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Test Notification -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold flex items-center gap-2">
                            <i class="fas fa-vial"></i>
                            알림 테스트
                        </h2>
                    </div>

                    <div class="card-content">
                        <div class="space-y-4">
                            <p class="text-gray-600">
                                알림 설정이 올바르게 구성되었는지 테스트하세요.
                            </p>

                            <!-- Custom Test Form -->
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        제목
                                    </label>
                                    <input
                                        v-model="testForm.title"
                                        type="text"
                                        class="input"
                                        placeholder="알림 제목"
                                    />
                                </div>

                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        알림 타입
                                    </label>
                                    <select v-model="testForm.notification_type" class="input">
                                        <option
                                            v-for="type in notificationTypes"
                                            :key="type.value"
                                            :value="type.value"
                                        >
                                            {{ type.label }}
                                        </option>
                                    </select>
                                </div>

                                <div class="md:col-span-2">
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        메시지
                                    </label>
                                    <textarea
                                        v-model="testForm.message"
                                        rows="3"
                                        class="input"
                                        placeholder="알림 메시지"
                                    ></textarea>
                                </div>

                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-2">
                                        우선순위
                                    </label>
                                    <select v-model="testForm.priority" class="input">
                                        <option
                                            v-for="priority in priorities"
                                            :key="priority.value"
                                            :value="priority.value"
                                        >
                                            {{ priority.label }}
                                        </option>
                                    </select>
                                </div>
                            </div>

                            <!-- Test Actions -->
                            <div class="flex flex-wrap gap-3">
                                <button
                                    @click="sendTestNotification"
                                    :disabled="testingNotification || !isNotificationConfigured"
                                    class="btn btn-primary"
                                    :class="{ 'opacity-50 cursor-not-allowed': testingNotification || !isNotificationConfigured }"
                                >
                                    <i class="fas" :class="testingNotification ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
                                    {{ testingNotification ? '전송 중...' : '커스텀 알림 전송' }}
                                </button>

                                <button
                                    @click="testWorkflowCompleteNotification"
                                    :disabled="testingNotification || !isNotificationConfigured"
                                    class="btn btn-secondary"
                                    :class="{ 'opacity-50 cursor-not-allowed': testingNotification || !isNotificationConfigured }"
                                >
                                    <i class="fas fa-check-circle"></i>
                                    워크플로우 완료 알림
                                </button>

                                <button
                                    @click="testWorkflowFailedNotification"
                                    :disabled="testingNotification || !isNotificationConfigured"
                                    class="btn btn-secondary"
                                    :class="{ 'opacity-50 cursor-not-allowed': testingNotification || !isNotificationConfigured }"
                                >
                                    <i class="fas fa-times-circle"></i>
                                    워크플로우 실패 알림
                                </button>
                            </div>

                            <!-- Test Result -->
                            <div v-if="testResult" class="mt-6">
                                <h3 class="font-semibold mb-3">테스트 결과</h3>

                                <div :class="testResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'" class="p-4 border rounded-lg mb-4">
                                    <div class="flex items-start gap-3">
                                        <i :class="testResult.success ? 'fa-check-circle text-green-600' : 'fa-times-circle text-red-600'" class="fas text-xl mt-1"></i>
                                        <div class="flex-1">
                                            <div class="font-semibold" :class="testResult.success ? 'text-green-900' : 'text-red-900'">
                                                {{ testResult.message }}
                                            </div>
                                            <div class="text-sm mt-1" :class="testResult.success ? 'text-green-800' : 'text-red-800'">
                                                {{ testResult.providers_succeeded }}개 제공자 성공 / {{ testResult.providers_attempted }}개 시도
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Provider Results -->
                                <div v-if="testResult.results" class="space-y-2">
                                    <div
                                        v-for="(result, idx) in testResult.results"
                                        :key="idx"
                                        class="flex items-center justify-between p-3 border rounded-lg"
                                        :class="result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'"
                                    >
                                        <div class="flex items-center gap-3">
                                            <i :class="getProviderIcon(result.provider)" class="fab text-gray-700"></i>
                                            <div>
                                                <div class="font-medium">{{ getProviderName(result.provider) }}</div>
                                                <div v-if="result.error" class="text-sm text-red-700">
                                                    {{ result.error }}
                                                </div>
                                                <div v-else-if="result.metadata" class="text-xs text-gray-600">
                                                    <span v-if="result.metadata.recipients">
                                                        수신자: {{ result.metadata.recipients.join(', ') }}
                                                    </span>
                                                    <span v-if="result.metadata.channel">
                                                        채널: {{ result.metadata.channel }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <i :class="result.success ? 'fa-check text-green-600' : 'fa-times text-red-600'" class="fas"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- System Information -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold flex items-center gap-2">
                            <i class="fas fa-info-circle"></i>
                            시스템 정보
                        </h2>
                    </div>

                    <div class="card-content">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div class="p-4 bg-gray-50 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">API 버전</div>
                                <div class="font-semibold">v1.0.0</div>
                            </div>

                            <div class="p-4 bg-gray-50 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">환경</div>
                                <div class="font-semibold">Production</div>
                            </div>

                            <div class="p-4 bg-gray-50 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">데이터베이스</div>
                                <div class="font-semibold">PostgreSQL</div>
                            </div>

                            <div class="p-4 bg-gray-50 rounded-lg">
                                <div class="text-sm text-gray-600 mb-1">작업 큐</div>
                                <div class="font-semibold">Celery + Redis</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Documentation Links -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="text-xl font-bold flex items-center gap-2">
                            <i class="fas fa-book"></i>
                            문서
                        </h2>
                    </div>

                    <div class="card-content">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <a href="/docs" target="_blank" class="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
                                <i class="fas fa-file-code text-blue-600 text-xl"></i>
                                <div>
                                    <div class="font-medium">API 문서</div>
                                    <div class="text-sm text-gray-600">FastAPI Swagger UI</div>
                                </div>
                            </a>

                            <a href="/docs/NOTIFICATIONS.md" target="_blank" class="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
                                <i class="fas fa-bell text-yellow-600 text-xl"></i>
                                <div>
                                    <div class="font-medium">알림 시스템</div>
                                    <div class="text-sm text-gray-600">이메일/Slack 설정 가이드</div>
                                </div>
                            </a>

                            <a href="/docs/SEO_SCORING.md" target="_blank" class="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
                                <i class="fas fa-chart-line text-green-600 text-xl"></i>
                                <div>
                                    <div class="font-medium">SEO 점수 계산</div>
                                    <div class="text-sm text-gray-600">콘텐츠 품질 검증 가이드</div>
                                </div>
                            </a>

                            <a href="/docs/ONE_CLICK_AUTOMATION.md" target="_blank" class="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
                                <i class="fas fa-magic text-purple-600 text-xl"></i>
                                <div>
                                    <div class="font-medium">원클릭 자동화</div>
                                    <div class="text-sm text-gray-600">완전 자동 파이프라인 가이드</div>
                                </div>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};
