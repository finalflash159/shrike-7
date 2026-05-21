package com.valtec.tts

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*

/**
 * Main Activity for Valtec Vietnamese TTS Demo.
 */
class MainActivity : AppCompatActivity() {
    
    private lateinit var textInput: EditText
    private lateinit var speakerSpinner: Spinner
    private lateinit var synthesizeButton: Button
    private lateinit var statusText: TextView
    
    private var audioTrack: AudioTrack? = null
    private val scope = CoroutineScope(Dispatchers.Main + Job())
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Initialize views
        textInput = findViewById(R.id.textInput)
        speakerSpinner = findViewById(R.id.speakerSpinner)
        synthesizeButton = findViewById(R.id.synthesizeButton)
        statusText = findViewById(R.id.statusText)
        
        // Setup spinner
        val speakers = arrayOf("Giọng nữ", "Giọng nam")
        speakerSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, speakers)
        
        // Setup button
        synthesizeButton.setOnClickListener {
            synthesize()
        }
        
        // Default text
        textInput.setText("Xin chào, chúc bạn một ngày tốt lành")
    }
    
    private fun synthesize() {
        val text = textInput.text.toString().trim()
        if (text.isEmpty()) {
            statusText.text = "⚠️ Vui lòng nhập văn bản"
            return
        }
        
        val speaker = if (speakerSpinner.selectedItemPosition == 0) "female" else "male"
        
        synthesizeButton.isEnabled = false
        statusText.text = "🔄 Đang tạo giọng nói..."
        
        scope.launch {
            try {
                // For demo, open HF Space in browser
                val intent = android.content.Intent(
                    android.content.Intent.ACTION_VIEW,
                    android.net.Uri.parse("https://huggingface.co/spaces/valtecAI-team/valtec-vietnamese-tts")
                )
                startActivity(intent)
                
                statusText.text = "✅ Đã mở demo trực tuyến"
                
            } catch (e: Exception) {
                statusText.text = "❌ Lỗi: ${e.message}"
            } finally {
                synthesizeButton.isEnabled = true
            }
        }
    }
    
    private fun playAudio(audioData: FloatArray, sampleRate: Int) {
        // Convert float to short
        val shortData = ShortArray(audioData.size) { i ->
            (audioData[i] * 32767).toInt().coerceIn(-32768, 32767).toShort()
        }
        
        audioTrack?.release()
        
        audioTrack = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_MEDIA)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setSampleRate(sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .build()
            )
            .setBufferSizeInBytes(shortData.size * 2)
            .setTransferMode(AudioTrack.MODE_STATIC)
            .build()
        
        audioTrack?.write(shortData, 0, shortData.size)
        audioTrack?.play()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        audioTrack?.release()
        scope.cancel()
    }
}
