import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export default function ConfigEditor() {
  const queryClient = useQueryClient()

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: api.config.get,
  })

  const updateConfig = useMutation({
    mutationFn: (voiceSettings) => api.config.update(voiceSettings),
    onSuccess: () => {
      queryClient.invalidateQueries(['config'])
      alert('Configuration updated successfully!')
    },
  })

  const [formData, setFormData] = useState({
    tts_provider: 'openai',
    openai_voice: 'nova',
    user_nickname: 'rockstar',
    personality: 'rockstar',
    language: 'en',
  })

  // Update form when config loads
  useState(() => {
    if (config?.voice_settings) {
      setFormData({ ...formData, ...config.voice_settings })
    }
  }, [config])

  const handleSubmit = (e) => {
    e.preventDefault()
    updateConfig.mutate(formData)
  }

  const voices = ['nova', 'alloy', 'echo', 'fable', 'onyx', 'shimmer']
  const personalities = ['rockstar', 'professional', 'minimal']
  const languages = [
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Spanish' },
  ]

  if (isLoading) {
    return <div className="text-white">Loading configuration...</div>
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">Configuration</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
          <h3 className="text-xl font-semibold text-white mb-4">Voice Settings</h3>

          <div className="space-y-4">
            {/* TTS Provider */}
            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                TTS Provider
              </label>
              <select
                value={formData.tts_provider}
                onChange={(e) => setFormData({ ...formData, tts_provider: e.target.value })}
                className="w-full px-4 py-2 bg-black/30 border border-purple-500/30 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="openai">OpenAI TTS</option>
                <option value="system">System TTS</option>
              </select>
            </div>

            {/* Voice Selection */}
            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                Preferred Voice
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {voices.map(voice => (
                  <button
                    key={voice}
                    type="button"
                    onClick={() => setFormData({ ...formData, openai_voice: voice })}
                    className={`px-4 py-2 rounded font-medium transition ${
                      formData.openai_voice === voice
                        ? 'bg-purple-600 text-white'
                        : 'bg-black/30 text-purple-200 hover:bg-purple-700/30'
                    }`}
                  >
                    {voice}
                  </button>
                ))}
              </div>
            </div>

            {/* Language */}
            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                Language
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="w-full px-4 py-2 bg-black/30 border border-purple-500/30 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                {languages.map(lang => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            {/* User Nickname */}
            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                Your Nickname
              </label>
              <input
                type="text"
                value={formData.user_nickname}
                onChange={(e) => setFormData({ ...formData, user_nickname: e.target.value })}
                className="w-full px-4 py-2 bg-black/30 border border-purple-500/30 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="rockstar"
              />
            </div>

            {/* Personality */}
            <div>
              <label className="block text-purple-200 text-sm font-medium mb-2">
                Personality Style
              </label>
              <div className="grid grid-cols-3 gap-2">
                {personalities.map(personality => (
                  <button
                    key={personality}
                    type="button"
                    onClick={() => setFormData({ ...formData, personality })}
                    className={`px-4 py-2 rounded font-medium transition ${
                      formData.personality === personality
                        ? 'bg-purple-600 text-white'
                        : 'bg-black/30 text-purple-200 hover:bg-purple-700/30'
                    }`}
                  >
                    {personality}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={updateConfig.isPending}
          className="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
        >
          {updateConfig.isPending ? 'Saving...' : '💾 Save Configuration'}
        </button>
      </form>

      <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
        <p className="text-blue-200 text-sm">
          <strong>💡 Tip:</strong> Changes are saved to config.json and take effect immediately for new voice notifications.
        </p>
      </div>
    </div>
  )
}
