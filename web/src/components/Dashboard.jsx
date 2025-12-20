import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export default function Dashboard() {
  const queryClient = useQueryClient()

  // Queries
  const { data: daemonStatus } = useQuery({
    queryKey: ['daemon', 'status'],
    queryFn: api.daemon.getStatus,
  })

  const { data: queueStatus } = useQuery({
    queryKey: ['queue', 'status'],
    queryFn: api.queue.getStatus,
  })

  // Mutations
  const startDaemon = useMutation({
    mutationFn: api.daemon.start,
    onSuccess: () => queryClient.invalidateQueries(['daemon']),
  })

  const stopDaemon = useMutation({
    mutationFn: api.daemon.stop,
    onSuccess: () => queryClient.invalidateQueries(['daemon']),
  })

  const restartDaemon = useMutation({
    mutationFn: api.daemon.restart,
    onSuccess: () => queryClient.invalidateQueries(['daemon']),
  })

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}h ${minutes}m ${secs}s`
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Dashboard</h2>

      {/* Daemon Status Card */}
      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <span>🎸</span> Daemon Status
          </h3>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block w-3 h-3 rounded-full ${
                daemonStatus?.running ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`}
            />
            <span className="text-white font-medium">
              {daemonStatus?.running ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-black/20 rounded p-4">
            <div className="text-purple-300 text-sm">PID</div>
            <div className="text-2xl font-bold text-white">
              {daemonStatus?.pid || 'N/A'}
            </div>
          </div>
          <div className="bg-black/20 rounded p-4">
            <div className="text-purple-300 text-sm">Uptime</div>
            <div className="text-2xl font-bold text-white">
              {daemonStatus?.uptime_seconds ? formatUptime(daemonStatus.uptime_seconds) : '0h 0m 0s'}
            </div>
          </div>
          <div className="bg-black/20 rounded p-4">
            <div className="text-purple-300 text-sm">Messages Processed</div>
            <div className="text-2xl font-bold text-white">
              {daemonStatus?.messages_processed || 0}
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => startDaemon.mutate()}
            disabled={daemonStatus?.running || startDaemon.isPending}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition"
          >
            {startDaemon.isPending ? 'Starting...' : '▶️ Start'}
          </button>
          <button
            onClick={() => stopDaemon.mutate()}
            disabled={!daemonStatus?.running || stopDaemon.isPending}
            className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition"
          >
            {stopDaemon.isPending ? 'Stopping...' : '⏸️ Stop'}
          </button>
          <button
            onClick={() => restartDaemon.mutate()}
            disabled={restartDaemon.isPending}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition"
          >
            {restartDaemon.isPending ? 'Restarting...' : '🔄 Restart'}
          </button>
        </div>
      </div>

      {/* Queue Status Card */}
      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <span>🎵</span> Message Queue
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-black/20 rounded p-4">
            <div className="text-purple-300 text-sm">Pending Messages</div>
            <div className="text-3xl font-bold text-white">
              {queueStatus?.pending_messages || 0}
            </div>
          </div>
          <div className="bg-black/20 rounded p-4">
            <div className="text-purple-300 text-sm">Queue Size</div>
            <div className="text-3xl font-bold text-white">
              {queueStatus?.size || 0}
            </div>
          </div>
        </div>

        {queueStatus?.pending_messages > 0 && (
          <div className="mt-4 p-3 bg-yellow-500/20 border border-yellow-500/30 rounded text-yellow-200">
            <p className="text-sm">
              💡 Tip: Go to the Queue tab to view and manage pending messages
            </p>
          </div>
        )}
      </div>

      {/* Info Card */}
      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <span>ℹ️</span> Quick Info
        </h3>
        <div className="space-y-2 text-purple-200">
          <p>• The daemon processes voice notifications in the background</p>
          <p>• Messages are queued and processed asynchronously</p>
          <p>• Use the tabs above to manage hooks, config, and test TTS</p>
        </div>
      </div>
    </div>
  )
}
