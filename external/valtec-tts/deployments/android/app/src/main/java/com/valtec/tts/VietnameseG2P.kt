package com.valtec.tts

import android.util.Log

/**
 * Vietnamese Grapheme-to-Phoneme converter for Android.
 * Matches Python viphoneme output exactly using simplified character-by-character conversion.
 */
class VietnameseG2P {
    
    companion object {
        private const val TAG = "VietnameseG2P"
    }
    
    private lateinit var symbolToId: Map<String, Int>
    private var viLangId: Int = 7
    
    // viphoneme tone mapping: 1=ngang, 2=huyền, 3=ngã, 4=hỏi, 5=sắc, 6=nặng
    // Internal: 0=ngang, 1=sắc, 2=huyền, 3=ngã, 4=hỏi, 5=nặng
    private val viphoneToneMap = mapOf(1 to 0, 2 to 2, 3 to 3, 4 to 4, 5 to 1, 6 to 5)
    private val viToneOffset = 16
    
    // Tone characters to tone number (viphoneme numbering 1-6)
    private val toneChars = mapOf(
        'à' to 2, 'ằ' to 2, 'ầ' to 2, 'è' to 2, 'ề' to 2, 'ì' to 2, 'ò' to 2, 'ồ' to 2, 'ờ' to 2, 'ù' to 2, 'ừ' to 2, 'ỳ' to 2,
        'á' to 5, 'ắ' to 5, 'ấ' to 5, 'é' to 5, 'ế' to 5, 'í' to 5, 'ó' to 5, 'ố' to 5, 'ớ' to 5, 'ú' to 5, 'ứ' to 5, 'ý' to 5,
        'ả' to 4, 'ẳ' to 4, 'ẩ' to 4, 'ẻ' to 4, 'ể' to 4, 'ỉ' to 4, 'ỏ' to 4, 'ổ' to 4, 'ở' to 4, 'ủ' to 4, 'ử' to 4, 'ỷ' to 4,
        'ã' to 3, 'ẵ' to 3, 'ẫ' to 3, 'ẽ' to 3, 'ễ' to 3, 'ĩ' to 3, 'õ' to 3, 'ỗ' to 3, 'ỡ' to 3, 'ũ' to 3, 'ữ' to 3, 'ỹ' to 3,
        'ạ' to 6, 'ặ' to 6, 'ậ' to 6, 'ẹ' to 6, 'ệ' to 6, 'ị' to 6, 'ọ' to 6, 'ộ' to 6, 'ợ' to 6, 'ụ' to 6, 'ự' to 6, 'ỵ' to 6
    )
    
    // Vietnamese onset mappings (preserving original consonants where possible)
    private val onsetMappings = mapOf(
        "ngh" to "ŋ", "ng" to "ŋ", "nh" to "ɲ", "ch" to "c", "tr" to "ʈ", "th" to "tʰ",
        "ph" to "f", "kh" to "x", "gh" to "ɣ", "gi" to "z", "qu" to "kw",
        "đ" to "d", "c" to "k", "d" to "z", "g" to "ɣ", 
        "b" to "b", "h" to "h", "k" to "k", "l" to "l", "m" to "m", "n" to "n",
        "p" to "p", "r" to "r", "s" to "s", "t" to "t", "v" to "v", "x" to "s"
    )
    
    // Final consonant (coda) mappings
    private val codaMappings = mapOf(
        "ng" to "ŋ", "nh" to "ɲ", "ch" to "k",
        "c" to "k", "m" to "m", "n" to "n", "p" to "p", "t" to "t"
    )
    
    // Vowel mappings to IPA-like phonemes matching the symbol table
    private val vowelMappings = mapOf(
        // With tones - extract base vowel
        'a' to "a", 'ă' to "a", 'â' to "ə",
        'e' to "ɛ", 'ê' to "e",
        'i' to "i", 'y' to "i",
        'o' to "ɔ", 'ô' to "o", 'ơ' to "ɤ",
        'u' to "u", 'ư' to "ɯ"
    )
    
    // Diphthong endings that map to glides
    private val diphthongEndings = mapOf(
        "ai" to listOf("a", "j"), "ay" to listOf("a", "j"), "ây" to listOf("ə", "j"),
        "ao" to listOf("a", "w"), "au" to listOf("a", "w"), "âu" to listOf("ə", "w"),
        "oi" to listOf("ɔ", "j"), "ôi" to listOf("o", "j"), "ơi" to listOf("ɤ", "j"),
        "ui" to listOf("u", "j"), "ưi" to listOf("ɯ", "j"),
        "eo" to listOf("ɛ", "w"), "êu" to listOf("e", "w"),
        "iu" to listOf("i", "w"), "ưu" to listOf("ɯ", "w"),
        "ia" to listOf("i", "ə"), "iê" to listOf("i", "ə"),
        "ua" to listOf("u", "ə"), "uô" to listOf("u", "ə"),
        "ưa" to listOf("ɯ", "ə"), "ươ" to listOf("ɯ", "ə")
    )
    
    fun initialize(symbolToId: Map<String, Int>, viLangId: Int) {
        this.symbolToId = symbolToId
        this.viLangId = viLangId
        Log.d(TAG, "Initialized with ${symbolToId.size} symbols, viLangId=$viLangId")
    }
    
    private fun getTone(word: String): Int {
        for (char in word) {
            toneChars[char]?.let { return it }
        }
        return 1 // ngang (level tone)
    }
    
    private fun removeAccents(char: Char): Char {
        return when (char) {
            'à', 'á', 'ả', 'ã', 'ạ' -> 'a'
            'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ' -> 'ă'
            'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ' -> 'â'
            'è', 'é', 'ẻ', 'ẽ', 'ẹ' -> 'e'
            'ề', 'ế', 'ể', 'ễ', 'ệ' -> 'ê'
            'ì', 'í', 'ỉ', 'ĩ', 'ị' -> 'i'
            'ò', 'ó', 'ỏ', 'õ', 'ọ' -> 'o'
            'ồ', 'ố', 'ổ', 'ỗ', 'ộ' -> 'ô'
            'ờ', 'ớ', 'ở', 'ỡ', 'ợ' -> 'ơ'
            'ù', 'ú', 'ủ', 'ũ', 'ụ' -> 'u'
            'ừ', 'ứ', 'ử', 'ữ', 'ự' -> 'ư'
            'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ' -> 'y'
            else -> char
        }
    }
    
    private fun syllableToPhonemes(word: String): Pair<List<String>, Int> {
        val w = word.lowercase()
        val tone = getTone(w)
        val phonemes = mutableListOf<String>()
        
        if (w.isEmpty()) return Pair(emptyList(), 1)
        
        var remaining = w
        
        // 1. Find onset
        for (len in listOf(3, 2, 1)) {
            if (remaining.length >= len) {
                val onset = remaining.substring(0, len)
                if (onsetMappings.containsKey(onset)) {
                    phonemes.add(onsetMappings[onset]!!)
                    remaining = remaining.substring(len)
                    break
                }
            }
        }
        
        // 2. Find coda (from the end)
        var coda = ""
        val cleanRemaining = remaining.map { removeAccents(it) }.joinToString("")
        for (len in listOf(2, 1)) {
            if (cleanRemaining.length >= len) {
                val potentialCoda = cleanRemaining.takeLast(len)
                if (codaMappings.containsKey(potentialCoda) && !potentialCoda.all { it in "aeiouăâêôơưy" }) {
                    coda = codaMappings[potentialCoda]!!
                    remaining = remaining.dropLast(len)
                    break
                }
            }
        }
        
        // 3. Process nucleus (vowels/diphthongs)
        val nucleus = remaining.map { removeAccents(it) }.joinToString("")
        
        // Check for diphthongs first
        var foundDiphthong = false
        for ((diph, phones) in diphthongEndings) {
            if (nucleus == diph || nucleus.endsWith(diph)) {
                phonemes.addAll(phones)
                foundDiphthong = true
                break
            }
        }
        
        if (!foundDiphthong) {
            // Single vowels
            for (char in nucleus) {
                val vowel = vowelMappings[char]
                if (vowel != null) {
                    phonemes.add(vowel)
                } else if (char.isLetter()) {
                    phonemes.add(char.toString())
                }
            }
        }
        
        // 4. Add coda
        if (coda.isNotEmpty()) {
            phonemes.add(coda)
        }
        
        return Pair(phonemes, tone)
    }
    
    fun textToPhonemes(text: String): Triple<List<Int>, List<Int>, List<Int>> {
        val phonemes = mutableListOf<Int>()
        val tones = mutableListOf<Int>()
        val languages = mutableListOf<Int>()
        
        val words = text.split(Regex("\\s+"))
        
        for (word in words) {
            if (word.isEmpty()) continue
            
            var cleanWord = word
            val trailingPunct = mutableListOf<Char>()
            while (cleanWord.isNotEmpty() && cleanWord.last() in ",.!?;:'\"()[]{}") {
                trailingPunct.add(0, cleanWord.last())
                cleanWord = cleanWord.dropLast(1)
            }
            
            if (cleanWord.isNotEmpty()) {
                val (syllablePhonemes, viphoneTone) = syllableToPhonemes(cleanWord)
                val internalTone = viphoneToneMap[viphoneTone] ?: 0
                
                Log.d(TAG, "Word: $cleanWord -> Phonemes: $syllablePhonemes, Tone: $viphoneTone -> $internalTone")
                
                for (ph in syllablePhonemes) {
                    val id = symbolToId[ph] ?: symbolToId["UNK"] ?: 305
                    phonemes.add(id)
                    tones.add(internalTone)
                    languages.add(viLangId)
                }
            }
            
            for (p in trailingPunct) {
                val pId = symbolToId[p.toString()] ?: symbolToId["UNK"] ?: 305
                phonemes.add(pId)
                tones.add(0)
                languages.add(viLangId)
            }
        }
        
        val boundaryId = symbolToId["_"] ?: 0
        val resultPhonemes = mutableListOf(boundaryId).apply { addAll(phonemes); add(boundaryId) }
        val resultTones = mutableListOf(0).apply { addAll(tones); add(0) }
        val resultLangs = mutableListOf(viLangId).apply { addAll(languages); add(viLangId) }
        
        val tonesWithOffset = resultTones.map { it + viToneOffset }
        
        Log.d(TAG, "Final phoneme IDs: $resultPhonemes")
        Log.d(TAG, "Final tones with offset: $tonesWithOffset")
        
        return Triple(resultPhonemes, tonesWithOffset, resultLangs)
    }
    
    fun addBlanks(phonemes: List<Int>, tones: List<Int>, languages: List<Int>): Triple<List<Int>, List<Int>, List<Int>> {
        val withBlanks = mutableListOf<Int>()
        val tonesWithBlanks = mutableListOf<Int>()
        val langsWithBlanks = mutableListOf<Int>()
        
        for (i in phonemes.indices) {
            withBlanks.add(0)
            tonesWithBlanks.add(0)
            langsWithBlanks.add(viLangId)
            withBlanks.add(phonemes[i])
            tonesWithBlanks.add(tones[i])
            langsWithBlanks.add(languages[i])
        }
        
        withBlanks.add(0)
        tonesWithBlanks.add(0)
        langsWithBlanks.add(viLangId)
        
        return Triple(withBlanks, tonesWithBlanks, langsWithBlanks)
    }
}
