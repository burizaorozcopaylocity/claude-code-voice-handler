import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export default function HookManager() {
  const queryClient = useQueryClient()

  const { data: hooks, isLoading } = useQuery({
    queryKey: ['hooks'],
    queryFn: api.hooks.getAll,
  })

  const toggleHook = useMutation({
    mutationFn: ({ hookName, enabled }) => api.hooks.toggle(hookName, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries(['hooks'])
    },
  })

  const hookDescriptions = {
    SessionStart: 'Triggered when a new Claude Code session starts',
    UserPromptSubmit: 'Triggered when you submit a prompt to Claude',
    PreToolUse: 'Triggered before Claude uses a tool (Read, Write, Bash, etc.)',
    PostToolUse: 'Triggered after Claude completes using a tool',
    Stop: 'Triggered when Claude finishes processing',
    Notification: 'Triggered on permission requests and notifications',
    SubagentStop: 'Triggered when a subagent completes its task',
  }

  const recommendedHooks = ['SessionStart', 'UserPromptSubmit', 'Stop']

  if (isLoading) {
    return <div className="text-white">Loading hooks...</div>
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Hook Manager</h2>

      <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
        <p className="text-blue-200 text-sm">
          <strong>💡 Recommended:</strong> Keep only SessionStart, UserPromptSubmit, and Stop enabled
          for the best experience. PreToolUse and PostToolUse can be too frequent.
        </p>
      </div>

      <div className="space-y-3">
        {Object.entries(hooks || {}).map(([hookName, hookData]) => {
          const isRecommended = recommendedHooks.includes(hookName)
          const isEnabled = hookData.enabled

          return (
            <div
              key={hookName}
              className={`bg-white/5 backdrop-blur rounded-lg p-4 border ${
                isEnabled
                  ? 'border-green-500/50'
                  : 'border-purple-500/30'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold text-white">{hookName}</h3>
                    {isRecommended && (
                      <span className="px-2 py-0.5 bg-green-600/30 text-green-300 text-xs rounded">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-purple-200 text-sm">
                    {hookDescriptions[hookName]}
                  </p>
                </div>

                <label className="relative inline-flex items-center cursor-pointer ml-4">
                  <input
                    type="checkbox"
                    checked={isEnabled}
                    onChange={(e) => {
                      toggleHook.mutate({
                        hookName,
                        enabled: e.target.checked,
                      })
                    }}
                    className="sr-only peer"
                  />
                  <div className="w-14 h-7 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:start-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-green-600"></div>
                </label>
              </div>
            </div>
          )
        })}
      </div>

      <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-lg p-4">
        <p className="text-yellow-200 text-sm">
          <strong>⚠️ Note:</strong> Changes to hooks require modifying settings.json.
          Disabling a hook here will comment it out in the configuration.
          You can always re-enable hooks later.
        </p>
      </div>
    </div>
  )
}
