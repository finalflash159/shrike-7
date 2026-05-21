package com.valtec.tts

import android.content.Context
import ai.onnxruntime.*
import android.util.Log
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.nio.FloatBuffer
import java.nio.LongBuffer
import kotlin.math.ceil
import kotlin.math.exp

/**
 * Vietnamese TTS Engine using ONNX Runtime on-device inference.
 * Uses OnnxHelper.java to workaround Kotlin type compatibility issues.
 */
class ValtecTTSEngine(private val context: Context) {
    
    companion object {
        private const val TAG = "ValtecTTSEngine"
        const val SAMPLE_RATE = 24000
    }
    
    private var ortEnvironment: OrtEnvironment? = null
    private var textEncoder: OrtSession? = null
    private var durationPredictor: OrtSession? = null
    private var flow: OrtSession? = null
    private var decoder: OrtSession? = null
    
    private lateinit var symbolToId: Map<String, Int>
    private var viLangId: Int = 7
    private val g2p = VietnameseG2P()
    
    private var isInitialized = false
    
    suspend fun initialize() = withContext(Dispatchers.IO) {
        try {
            ortEnvironment = OrtEnvironment.getEnvironment()
            loadConfig()
            
            val options = OrtSession.SessionOptions()
            options.setOptimizationLevel(OrtSession.SessionOptions.OptLevel.BASIC_OPT)
            
            Log.d(TAG, "Loading ONNX models...")
            textEncoder = loadModel("text_encoder.onnx", options)
            Log.d(TAG, "  ✓ text_encoder")
            durationPredictor = loadModel("duration_predictor.onnx", options)
            Log.d(TAG, "  ✓ duration_predictor")
            flow = loadModel("flow.onnx", options) 
            Log.d(TAG, "  ✓ flow")
            decoder = loadModel("decoder.onnx", options)
            Log.d(TAG, "  ✓ decoder")
            
            isInitialized = true
            Log.d(TAG, "All models loaded successfully")
        } catch (e: Exception) {
            Log.e(TAG, "Init failed: ${e.message}", e)
            throw e
        }
    }
    
    private fun loadConfig() {
        val configJson = context.assets.open("tts_config.json").bufferedReader().readText()
        val gson = Gson()
        val config = gson.fromJson<Map<String, Any>>(configJson, object : TypeToken<Map<String, Any>>() {}.type)
        
        @Suppress("UNCHECKED_CAST")
        val symbolToIdRaw = config["symbol_to_id"] as? Map<String, Double> ?: emptyMap()
        symbolToId = symbolToIdRaw.mapValues { it.value.toInt() }
        
        @Suppress("UNCHECKED_CAST")
        val langIdMap = config["language_id_map"] as? Map<String, Double> ?: emptyMap()
        viLangId = langIdMap["VI"]?.toInt() ?: 7
        
        g2p.initialize(symbolToId, viLangId)
        Log.d(TAG, "Config loaded: ${symbolToId.size} symbols")
    }
    
    private fun loadModel(fileName: String, options: OrtSession.SessionOptions): OrtSession {
        val modelBytes = context.assets.open(fileName).readBytes()
        return ortEnvironment!!.createSession(modelBytes, options)
    }

    suspend fun synthesize(
        text: String,
        speakerId: Int = 1,
        noiseScale: Float = 0.667f,
        lengthScale: Float = 1.0f
    ): FloatArray = withContext(Dispatchers.IO) {
        
        if (!isInitialized) throw IllegalStateException("Not initialized")
        val env = ortEnvironment!!
        
        Log.d(TAG, "Synthesizing: \"$text\"")
        
        // G2P conversion
        val (phonemes, tones, languages) = g2p.textToPhonemes(text)
        Log.d(TAG, "Phonemes: $phonemes")
        Log.d(TAG, "Tones: $tones")
        val (pBlanks, tBlanks, lBlanks) = g2p.addBlanks(phonemes, tones, languages)
        val seqLen = pBlanks.size
        Log.d(TAG, "Phonemes with blanks: $seqLen, first 20: ${pBlanks.take(20)}")
        
        // Create input tensors
        val phoneIds = OnnxTensor.createTensor(env, LongBuffer.wrap(pBlanks.map{it.toLong()}.toLongArray()), longArrayOf(1, seqLen.toLong()))
        val phoneLengths = OnnxTensor.createTensor(env, LongBuffer.wrap(longArrayOf(seqLen.toLong())), longArrayOf(1))
        val toneIds = OnnxTensor.createTensor(env, LongBuffer.wrap(tBlanks.map{it.toLong()}.toLongArray()), longArrayOf(1, seqLen.toLong()))
        val languageIds = OnnxTensor.createTensor(env, LongBuffer.wrap(lBlanks.map{it.toLong()}.toLongArray()), longArrayOf(1, seqLen.toLong()))
        val bert = OnnxTensor.createTensor(env, FloatBuffer.wrap(FloatArray(1024*seqLen)), longArrayOf(1,1024,seqLen.toLong()))
        val jaBert = OnnxTensor.createTensor(env, FloatBuffer.wrap(FloatArray(768*seqLen)), longArrayOf(1,768,seqLen.toLong()))
        val sid = OnnxTensor.createTensor(env, LongBuffer.wrap(longArrayOf(speakerId.toLong())), longArrayOf(1))
        
        try {
            // Text encoder - use Java helper
            val encInputs = hashMapOf<String, OnnxTensor>(
                "phone_ids" to phoneIds,
                "phone_lengths" to phoneLengths,
                "tone_ids" to toneIds,
                "language_ids" to languageIds,
                "bert" to bert,
                "ja_bert" to jaBert,
                "speaker_id" to sid
            )
            Log.d(TAG, "Running text encoder...")
            val encResult = OnnxHelper.runWithTensors(textEncoder, encInputs)
            
            val mPTensor = encResult[1] as OnnxTensor
            val logsPTensor = encResult[2] as OnnxTensor
            val xMaskTensor = encResult[3] as OnnxTensor
            val channels = mPTensor.info.shape[1].toInt()
            
            // Duration predictor
            val dpInputs = hashMapOf<String, OnnxValue>(
                "x" to encResult[0],
                "x_mask" to encResult[3],
                "g" to encResult[4]
            )
            Log.d(TAG, "Running duration predictor...")
            val dpResult = OnnxHelper.runWithValues(durationPredictor, dpInputs)
            
            val logwTensor = dpResult[0] as OnnxTensor
            val logwData = logwTensor.floatBuffer
            val xMaskData = xMaskTensor.floatBuffer
            
            // Compute durations
            var totalFrames = 0
            val durations = IntArray(seqLen) { t ->
                val dur = ceil(exp(logwData.get(t).toDouble()) * xMaskData.get(t) * lengthScale).toInt()
                totalFrames += dur
                dur
            }
            if(totalFrames==0) totalFrames=1
            Log.d(TAG, "Total frames: $totalFrames")
            
            // Expand m_p and logs_p
            val mPData = mPTensor.floatBuffer
            val logsPData = logsPTensor.floatBuffer
            val expandedMp = FloatArray(channels * totalFrames)
            val expandedLogsP = FloatArray(channels * totalFrames)
            
            var fIdx = 0
            for(t in 0 until seqLen) {
                for(d in 0 until durations[t]) {
                    if(fIdx < totalFrames) {
                        for(c in 0 until channels) {
                            expandedMp[c*totalFrames+fIdx] = mPData.get(c*seqLen+t)
                            expandedLogsP[c*totalFrames+fIdx] = logsPData.get(c*seqLen+t)
                        }
                        fIdx++
                    }
                }
            }
            
            // Sample z_p
            val rand = java.util.Random()
            val zPData = FloatArray(channels*totalFrames) { i ->
                expandedMp[i] + exp(expandedLogsP[i].toDouble()).toFloat() * rand.nextGaussian().toFloat() * noiseScale
            }
            
            val zPTensor = OnnxTensor.createTensor(env, FloatBuffer.wrap(zPData), longArrayOf(1,channels.toLong(),totalFrames.toLong()))
            val yMask = OnnxTensor.createTensor(env, FloatBuffer.wrap(FloatArray(totalFrames){1f}), longArrayOf(1,1,totalFrames.toLong()))
            
            // Flow
            val flowInputs = hashMapOf<String, OnnxValue>("z_p" to zPTensor, "y_mask" to yMask, "g" to encResult[4])
            Log.d(TAG, "Running flow...")
            val flowResult = OnnxHelper.runWithValues(flow, flowInputs)
            
            // Decoder
            val decInputs = hashMapOf<String, OnnxValue>("z" to flowResult[0], "g" to encResult[4])
            Log.d(TAG, "Running decoder...")
            val decResult = OnnxHelper.runWithValues(decoder, decInputs)
            
            // Extract audio
            val audioTensor = decResult[0] as OnnxTensor
            val audioBuffer = audioTensor.floatBuffer
            val audio = FloatArray(audioBuffer.remaining())
            audioBuffer.get(audio)
            
            // Cleanup
            encResult.close(); dpResult.close(); flowResult.close(); decResult.close()
            zPTensor.close(); yMask.close()
            
            Log.d(TAG, "Generated ${audio.size} samples")
            audio
            
        } finally {
            phoneIds.close(); phoneLengths.close(); toneIds.close()
            languageIds.close(); bert.close(); jaBert.close(); sid.close()
        }
    }
    
    fun close() {
        textEncoder?.close(); durationPredictor?.close(); flow?.close(); decoder?.close()
        ortEnvironment?.close()
        isInitialized = false
    }
}
