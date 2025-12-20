import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

export default function TTSTester() {
  const [text, setText] = useState('')
  const [voice, setVoice] = useState('nova')

  const testTTS = useMutation({
    mutationFn: () => api.tts.test(text, voice),
    onSuccess: () => {
      alert('TTS test queued! Listen for the audio.')
    },
  })

  const voices = ['nova', 'alloy', 'echo', 'fable', 'onyx', 'shimmer']

  const quickTestPhrases = [
    '¡Shine on you crazy coder!',
    'Let it flow! Claude is reading your code like Gilmour reading sheet music.',
    'Testing, one two three!',
    'The show must go on!',
    '¡Heavy! Claude va a crear un SPA épico.',
  ]

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-white">TTS Tester</h2>

      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <div className="space-y-4">
          {/* Text Input */}
          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Message to Speak
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={4}
              className="w-full px-4 py-2 bg-black/30 border border-purple-500/30 rounded text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Enter text to test TTS..."
            />
          </div>

          {/* Voice Selection */}
          <div>
            <label className="block text-purple-200 text-sm font-medium mb-2">
              Select Voice
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {voices.map(v => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setVoice(v)}
                  className={`px-4 py-2 rounded font-medium transition ${
                    voice === v
                      ? 'bg-purple-600 text-white'
                      : 'bg-black/30 text-purple-200 hover:bg-purple-700/30'
                  }`}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>

          {/* Test Button */}
          <button
            onClick={() => testTTS.mutate()}
            disabled={!text || testTTS.isPending}
            className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition"
          >
            {testTTS.isPending ? 'Queueing...' : '🎤 Test Voice'}
          </button>
        </div>
      </div>

      {/* Quick Test Phrases */}
      <div className="bg-white/5 backdrop-blur rounded-lg p-6 border border-purple-500/30">
        <h3 className="text-lg font-semibold text-white mb-4">Quick Test Phrases</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {quickTestPhrases.map((phrase, index) => (
            <button
              key={index}
              onClick={() => setText(phrase)}
              className="px-4 py-2 bg-black/30 hover:bg-purple-700/30 text-purple-200 rounded text-left text-sm transition"
            >
              {phrase}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-4">
        <p className="text-blue-200 text-sm">
          <strong>💡 How it works:</strong> When you click "Test Voice", the message is queued
          in the voice daemon. You should hear it play through your speakers shortly after.
        </p>
      </div>
    </div>
  )
}
