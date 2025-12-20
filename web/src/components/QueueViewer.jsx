import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export default function QueueViewer() {
  const queryClient = useQueryClient()

  const { data: queueStatus } = useQuery({
    queryKey: ['queue', 'status'],
    queryFn: api.queue.getStatus,
  })

  const clearQueue = useMutation({
    mutationFn: api.queue.clear,
    onSuccess: () => {
      queryClient.invalidateQueries(['queue'])
      alert('Queue cleared successfully!')
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Message Queue</h2>
        <button
          onClick={() => {
            if (confirm('Are you sure you want to clear all pending messages?')) {
              clearQueue.mutate()
            }
          }}
          disabled={!queueStatus?.size || clearQueue.isPending}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded font-medium transition"
        >
          {clearQueue.isPending ? 'Clearing...' : '🧹 Clear Queue'}
        </button>
      </div>

      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <div className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-black/20 rounded p-4">
              <div className="text-purple-300 text-sm">Total Messages</div>
              <div className="text-3xl font-bold text-white">
                {queueStatus?.size || 0}
              </div>
            </div>
            <div className="bg-black/20 rounded p-4">
              <div className="text-purple-300 text-sm">Pending</div>
              <div className="text-3xl font-bold text-white">
                {queueStatus?.pending_messages || 0}
              </div>
            </div>
          </div>
        </div>

        {queueStatus?.size === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎵</div>
            <p className="text-purple-200 text-lg">No messages in queue</p>
            <p className="text-purple-300 text-sm mt-2">
              The queue is empty - all voice notifications have been processed!
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-yellow-500/20 border border-yellow-500/30 rounded">
              <p className="text-yellow-200 text-sm">
                <strong>Note:</strong> Queue details are managed by the SQLite backend.
                Messages are processed in priority order by the daemon.
              </p>
            </div>

            <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded">
              <p className="text-blue-200 text-sm">
                <strong>Tip:</strong> If there are too many pending messages, use the "Clear Queue"
                button to reset the queue. The daemon will continue processing new messages normally.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
