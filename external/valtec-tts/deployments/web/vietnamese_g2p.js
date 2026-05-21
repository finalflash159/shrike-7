/**
 * Vietnamese Grapheme-to-Phoneme (G2P) Converter for Browser
 * Ported from viphoneme library (https://github.com/v-nhandt21/Viphoneme)
 * 
 * This implements the full Vietnamese phonemizer logic including:
 * - Onset detection (trigraphs like 'ngh', digraphs like 'ng', 'nh', 'ch')
 * - Nucleus (vowel) conversion with diphthongs
 * - Coda (final consonant) handling
 * - Tone extraction from diacritics
 * - Onglides, offglides combinations
 */

// ============================================================
// PHONEME MAPPINGS (from viphoneme T2IPA.py - Cus_* dictionaries)
// ============================================================

// Onset consonants
const Cus_onsets = {
    'b': 'b', 't': 't', 'th': 'tʰ', 'đ': 'd', 'ch': 'c',
    'kh': 'x', 'g': 'ɣ', 'l': 'l', 'm': 'm', 'n': 'n',
    'ngh': 'ŋ', 'nh': 'ɲ', 'ng': 'ŋ', 'ph': 'f', 'v': 'v',
    'x': 's', 'd': 'z', 'h': 'h', 'p': 'p', 'qu': 'kw',
    'gi': 'j', 'tr': 'ʈ', 'k': 'k', 'c': 'k', 'gh': 'ɣ',
    'r': 'ʐ', 's': 'ʂ'
};

// Nuclei (vowels and diphthongs)
const Cus_nuclei = {
    // Single vowels
    'a': 'a', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'â': 'ɤ̆', 'ấ': 'ɤ̆', 'ầ': 'ɤ̆', 'ẩ': 'ɤ̆', 'ẫ': 'ɤ̆', 'ậ': 'ɤ̆',
    'ă': 'ă', 'ắ': 'ă', 'ằ': 'ă', 'ẳ': 'ă', 'ẵ': 'ă', 'ặ': 'ă',
    'e': 'ɛ', 'é': 'ɛ', 'è': 'ɛ', 'ẻ': 'ɛ', 'ẽ': 'ɛ', 'ẹ': 'ɛ',
    'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'i': 'i', 'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'o': 'ɔ', 'ó': 'ɔ', 'ò': 'ɔ', 'ỏ': 'ɔ', 'õ': 'ɔ', 'ọ': 'ɔ',
    'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
    'ơ': 'ɤ', 'ớ': 'ɤ', 'ờ': 'ɤ', 'ở': 'ɤ', 'ỡ': 'ɤ', 'ợ': 'ɤ',
    'u': 'u', 'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'ư': 'ɯ', 'ứ': 'ɯ', 'ừ': 'ɯ', 'ử': 'ɯ', 'ữ': 'ɯ', 'ự': 'ɯ',
    'y': 'i', 'ý': 'i', 'ỳ': 'i', 'ỷ': 'i', 'ỹ': 'i', 'ỵ': 'i',

    // Diphthongs
    'eo': 'eo', 'éo': 'eo', 'èo': 'eo', 'ẻo': 'eo', 'ẽo': 'eo', 'ẹo': 'eo',
    'êu': 'ɛu', 'ếu': 'ɛu', 'ều': 'ɛu', 'ểu': 'ɛu', 'ễu': 'ɛu', 'ệu': 'ɛu',
    'ia': 'iə', 'ía': 'iə', 'ìa': 'iə', 'ỉa': 'iə', 'ĩa': 'iə', 'ịa': 'iə',
    'iá': 'iə', 'ià': 'iə', 'iả': 'iə', 'iã': 'iə', 'iạ': 'iə',
    'iê': 'iə', 'iế': 'iə', 'iề': 'iə', 'iể': 'iə', 'iễ': 'iə', 'iệ': 'iə',
    'oo': 'ɔ', 'óo': 'ɔ', 'òo': 'ɔ', 'ỏo': 'ɔ', 'õo': 'ɔ', 'ọo': 'ɔ',
    'oó': 'ɔ', 'oò': 'ɔ', 'oỏ': 'ɔ', 'oõ': 'ɔ', 'oọ': 'ɔ',
    'ua': 'uə', 'úa': 'uə', 'ùa': 'uə', 'ủa': 'uə', 'ũa': 'uə', 'ụa': 'uə',
    'uô': 'uə', 'uố': 'uə', 'uồ': 'uə', 'uổ': 'uə', 'uỗ': 'uə', 'uộ': 'uə',
    'ưa': 'ɯə', 'ứa': 'ɯə', 'ừa': 'ɯə', 'ửa': 'ɯə', 'ữa': 'ɯə', 'ựa': 'ɯə',
    'ươ': 'ɯə', 'ướ': 'ɯə', 'ườ': 'ɯə', 'ưở': 'ɯə', 'ưỡ': 'ɯə', 'ượ': 'ɯə',
    'yê': 'iɛ', 'yế': 'iɛ', 'yề': 'iɛ', 'yể': 'iɛ', 'yễ': 'iɛ', 'yệ': 'iɛ',
    'uơ': 'uə', 'uở': 'uə', 'uờ': 'uə', 'uỡ': 'uə', 'uợ': 'uə',
};

// Offglides
const Cus_offglides = {
    'ai': 'aj', 'ái': 'aj', 'ài': 'aj', 'ải': 'aj', 'ãi': 'aj', 'ại': 'aj',
    'ay': 'ăj', 'áy': 'ăj', 'ày': 'ăj', 'ảy': 'ăj', 'ãy': 'ăj', 'ạy': 'ăj',
    'ao': 'aw', 'áo': 'aw', 'ào': 'aw', 'ảo': 'aw', 'ão': 'aw', 'ạo': 'aw',
    'au': 'ăw', 'áu': 'ăw', 'àu': 'ăw', 'ảu': 'ăw', 'ãu': 'ăw', 'ạu': 'ăw',
    'ây': 'ɤ̆j', 'ấy': 'ɤ̆j', 'ầy': 'ɤ̆j', 'ẩy': 'ɤ̆j', 'ẫy': 'ɤ̆j', 'ậy': 'ɤ̆j',
    'âu': 'ɤ̆w', 'ấu': 'ɤ̆w', 'ầu': 'ɤ̆w', 'ẩu': 'ɤ̆w', 'ẫu': 'ɤ̆w', 'ậu': 'ɤ̆w',
    'eo': 'ew', 'éo': 'ew', 'èo': 'ew', 'ẻo': 'ew', 'ẽo': 'ew', 'ẹo': 'ew',
    'iu': 'iw', 'íu': 'iw', 'ìu': 'iw', 'ỉu': 'iw', 'ĩu': 'iw', 'ịu': 'iw',
    'oi': 'ɔj', 'ói': 'ɔj', 'òi': 'ɔj', 'ỏi': 'ɔj', 'õi': 'ɔj', 'ọi': 'ɔj',
    'ôi': 'oj', 'ối': 'oj', 'ồi': 'oj', 'ổi': 'oj', 'ỗi': 'oj', 'ội': 'oj',
    'ui': 'uj', 'úi': 'uj', 'ùi': 'uj', 'ủi': 'uj', 'ũi': 'uj', 'ụi': 'uj',
    'uy': 'ʷi', 'úy': 'uj', 'ùy': 'uj', 'ủy': 'uj', 'ũy': 'uj', 'ụy': 'uj',
    'uý': 'ʷi', 'uỳ': 'ʷi', 'uỷ': 'ʷi', 'uỹ': 'ʷi', 'uỵ': 'ʷi',
    'ơi': 'ɤj', 'ới': 'ɤj', 'ời': 'ɤj', 'ởi': 'ɤj', 'ỡi': 'ɤj', 'ợi': 'ɤj',
    'ưi': 'ɯj', 'ứi': 'ɯj', 'ừi': 'ɯj', 'ửi': 'ɯj', 'ữi': 'ɯj', 'ựi': 'ɯj',
    'ưu': 'ɯw', 'ứu': 'ɯw', 'ừu': 'ɯw', 'ửu': 'ɯw', 'ữu': 'ɯw', 'ựu': 'ɯw',

    // Triphthongs
    'iêu': 'iəw', 'iếu': 'iəw', 'iều': 'iəw', 'iểu': 'iəw', 'iễu': 'iəw', 'iệu': 'iəw',
    'yêu': 'iəw', 'yếu': 'iəw', 'yều': 'iəw', 'yểu': 'iəw', 'yễu': 'iəw', 'yệu': 'iəw',
    'uôi': 'uəj', 'uối': 'uəj', 'uồi': 'uəj', 'uổi': 'uəj', 'uỗi': 'uəj', 'uội': 'uəj',
    'ươi': 'ɯəj', 'ưới': 'ɯəj', 'ười': 'ɯəj', 'ưởi': 'ɯəj', 'ưỡi': 'ɯəj', 'ượi': 'ɯəj',
    'ươu': 'ɯəw', 'ướu': 'ɯəw', 'ườu': 'ɯəw', 'ưởu': 'ɯəw', 'ưỡu': 'ɯəw', 'ượu': 'ɯəw',
};

// Onglides (labialized consonants)
const Cus_onglides = {
    'oa': 'ʷa', 'oá': 'ʷa', 'oà': 'ʷa', 'oả': 'ʷa', 'oã': 'ʷa', 'oạ': 'ʷa',
    'óa': 'ʷa', 'òa': 'ʷa', 'ỏa': 'ʷa', 'õa': 'ʷa', 'ọa': 'ʷa',
    'oă': 'ʷă', 'oắ': 'ʷă', 'oằ': 'ʷă', 'oẳ': 'ʷă', 'oẵ': 'ʷă', 'oặ': 'ʷă',
    'oe': 'ʷɛ', 'oé': 'ʷɛ', 'oè': 'ʷɛ', 'oẻ': 'ʷɛ', 'oẽ': 'ʷɛ', 'oẹ': 'ʷɛ',
    'óe': 'ʷɛ', 'òe': 'ʷɛ', 'ỏe': 'ʷɛ', 'õe': 'ʷɛ', 'ọe': 'ʷɛ',
    'ua': 'ʷa', 'uá': 'ʷa', 'uà': 'ʷa', 'uả': 'ʷa', 'uã': 'ʷa', 'uạ': 'ʷa',
    'uă': 'ʷă', 'uắ': 'ʷă', 'uằ': 'ʷă', 'uẳ': 'ʷă', 'uẵ': 'ʷă', 'uặ': 'ʷă',
    'uâ': 'ʷɤ̆', 'uấ': 'ʷɤ̆', 'uầ': 'ʷɤ̆', 'uẩ': 'ʷɤ̆', 'uẫ': 'ʷɤ̆', 'uậ': 'ʷɤ̆',
    'ue': 'ʷɛ', 'ué': 'ʷɛ', 'uè': 'ʷɛ', 'uẻ': 'ʷɛ', 'uẽ': 'ʷɛ', 'uẹ': 'ʷɛ',
    'uê': 'ʷe', 'uế': 'ʷe', 'uề': 'ʷe', 'uể': 'ʷe', 'uễ': 'ʷe', 'uệ': 'ʷe',
    'uơ': 'ʷɤ', 'uớ': 'ʷɤ', 'uờ': 'ʷɤ', 'uở': 'ʷɤ', 'uỡ': 'ʷɤ', 'uợ': 'ʷɤ',
    'uy': 'ʷi', 'uý': 'ʷi', 'uỳ': 'ʷi', 'uỷ': 'ʷi', 'uỹ': 'ʷi', 'uỵ': 'ʷi',
    'uya': 'ʷiə', 'uyá': 'ʷiə', 'uyà': 'ʷiə', 'uyả': 'ʷiə', 'uyã': 'ʷiə', 'uyạ': 'ʷiə',
    'uyê': 'ʷiə', 'uyế': 'ʷiə', 'uyề': 'ʷiə', 'uyể': 'ʷiə', 'uyễ': 'ʷiə', 'uyệ': 'ʷiə',
    // uớ needs special handling - it's w + ʷɔ (labialized)
    'uớ': 'ʷɔ', 'uờ': 'ʷɔ', 'uở': 'ʷɔ', 'uỡ': 'ʷɔ', 'uợ': 'ʷɔ',
};

// Onoff glides
const Cus_onoffglides = {
    'oai': 'aj', 'oái': 'aj', 'oài': 'aj', 'oải': 'aj', 'oãi': 'aj', 'oại': 'aj',
    'oay': 'ăj', 'oáy': 'ăj', 'oày': 'ăj', 'oảy': 'ăj', 'oãy': 'ăj', 'oạy': 'ăj',
    'oao': 'aw', 'oáo': 'aw', 'oào': 'aw', 'oảo': 'aw', 'oão': 'aw', 'oạo': 'aw',
    'oeo': 'ew', 'oéo': 'ew', 'oèo': 'ew', 'oẻo': 'ew', 'oẽo': 'ew', 'oẹo': 'ew',
    'uai': 'aj', 'uái': 'aj', 'uài': 'aj', 'uải': 'aj', 'uãi': 'aj', 'uại': 'aj',
    'uay': 'ăj', 'uáy': 'ăj', 'uày': 'ăj', 'uảy': 'ăj', 'uãy': 'ăj', 'uạy': 'ăj',
    'uây': 'ɤ̆j', 'uấy': 'ɤ̆j', 'uầy': 'ɤ̆j', 'uẩy': 'ɤ̆j', 'uẫy': 'ɤ̆j', 'uậy': 'ɤ̆j',
};

// Coda consonants
const Cus_codas = {
    'p': 'p', 't': 't', 'c': 'k', 'm': 'm', 'n': 'n', 'ng': 'ŋ', 'nh': 'ɲ', 'ch': 'tʃ'
};

// Tone markers (diacritics to tone numbers)
const Cus_tones_p = {
    'á': 5, 'à': 2, 'ả': 4, 'ã': 3, 'ạ': 6,
    'ấ': 5, 'ầ': 2, 'ẩ': 4, 'ẫ': 3, 'ậ': 6,
    'ắ': 5, 'ằ': 2, 'ẳ': 4, 'ẵ': 3, 'ặ': 6,
    'é': 5, 'è': 2, 'ẻ': 4, 'ẽ': 3, 'ẹ': 6,
    'ế': 5, 'ề': 2, 'ể': 4, 'ễ': 3, 'ệ': 6,
    'í': 5, 'ì': 2, 'ỉ': 4, 'ĩ': 3, 'ị': 6,
    'ó': 5, 'ò': 2, 'ỏ': 4, 'õ': 3, 'ọ': 6,
    'ố': 5, 'ồ': 2, 'ổ': 4, 'ỗ': 3, 'ộ': 6,
    'ớ': 5, 'ờ': 2, 'ở': 4, 'ỡ': 3, 'ợ': 6,
    'ú': 5, 'ù': 2, 'ủ': 4, 'ũ': 3, 'ụ': 6,
    'ứ': 5, 'ừ': 2, 'ử': 4, 'ữ': 3, 'ự': 6,
    'ý': 5, 'ỳ': 2, 'ỷ': 4, 'ỹ': 3, 'ỵ': 6,
};

// Special cases
const Cus_gi = {
    'gi': 'zi', 'gí': 'zi', 'gì': 'zi', 'gỉ': 'zi', 'gĩ': 'zi', 'gị': 'zi',
};
// Extended gi patterns - full word matches
const Cus_gi_extended = {
    'giáng': 'jaŋ', 'giàng': 'jaŋ', 'giảng': 'jaŋ', 'giãng': 'jaŋ', 'giạng': 'jaŋ',
    'giá': 'ja', 'già': 'ja', 'giả': 'ja', 'giã': 'ja', 'giạ': 'ja',
};
const Cus_qu = {
    'quy': 'kwi', 'qúy': 'kwi', 'qùy': 'kwi', 'qủy': 'kwi', 'qũy': 'kwi', 'qụy': 'kwi'
};

// ============================================================
// CORE FUNCTIONS
// ============================================================

/**
 * Transcribe a Vietnamese word to IPA with tone
 * @param {string} word - Vietnamese word
 * @returns {object} - {ons, nuc, cod, ton}
 */
function trans(word) {
    word = word.toLowerCase();

    let ons = '';
    let nuc = '';
    let cod = '';
    let ton = 1; // default tone (ngang)
    let oOffset = 0;
    let cOffset = 0;
    const l = word.length;

    if (l === 0) return { ons, nuc, cod, ton };

    // Detect onset
    if (word.substring(0, 3) in Cus_onsets) {
        ons = Cus_onsets[word.substring(0, 3)];
        oOffset = 3;
    } else if (word.substring(0, 2) in Cus_onsets) {
        ons = Cus_onsets[word.substring(0, 2)];
        oOffset = 2;
    } else if (word[0] in Cus_onsets) {
        ons = Cus_onsets[word[0]];
        oOffset = 1;
    }

    // Detect coda
    if (word.substring(l - 2) in Cus_codas) {
        cod = Cus_codas[word.substring(l - 2)];
        cOffset = 2;
    } else if (word[l - 1] in Cus_codas) {
        cod = Cus_codas[word[l - 1]];
        cOffset = 1;
    }

    // Get nucleus
    let nucl = word.substring(oOffset, l - cOffset);

    // Handle special 'gi' case based on Python viphoneme analysis:
    // - 'gi' standalone → 'z' onset (Cus_gi handles this)
    // - 'gì', 'gí', 'gĩ', 'gị' standalone → 'ɣ' onset (handled by Cus_onsets 'g')
    // - 'gim', 'gít', 'gìn', 'gín', 'gĩn', 'gịn' (3 chars, gi+coda, i NOT ỉ) → 'z' onset
    // - 'gỉm', 'gỉt', 'gỉn' (g + ỉ + coda) → 'ɣ' onset (ỉ tone breaks special case)
    // - 'giểm', 'giám' (gi + other vowel + coda) → 'j' onset (via Cus_onsets 'gi')
    const iVariantsExceptHoi = 'iíìĩị'; // All i variants except ỉ (tone hỏi)
    if (word[0] === 'g' && word.length === 3 && iVariantsExceptHoi.includes(word[1]) && cod) {
        // gi + coda (exactly 3 chars) like 'gim', 'gít', 'gịn' → z + i + coda
        nucl = 'i';
        ons = 'z';
    }

    // Try to match nucleus
    if (nucl in Cus_nuclei) {
        nuc = Cus_nuclei[nucl];
    } else if (nucl in Cus_onglides && ons !== 'kw') {
        nuc = Cus_onglides[nucl];
        if (ons) {
            ons = ons + 'w';
        } else {
            ons = 'w';
        }
    } else if (nucl in Cus_onglides && ons === 'kw') {
        nuc = Cus_onglides[nucl];
    } else if (nucl in Cus_onoffglides) {
        const glide = Cus_onoffglides[nucl];
        cod = glide[glide.length - 1];
        nuc = glide.substring(0, glide.length - 1);
        if (ons !== 'kw') {
            if (ons) {
                ons = ons + 'w';
            } else {
                ons = 'w';
            }
        }
    } else if (nucl in Cus_offglides) {
        const glide = Cus_offglides[nucl];
        cod = glide[glide.length - 1];
        nuc = glide.substring(0, glide.length - 1);
    } else if (word in Cus_gi) {
        ons = Cus_gi[word][0];
        nuc = Cus_gi[word][1];
    } else if (word in Cus_qu) {
        const qu = Cus_qu[word];
        ons = qu.substring(0, qu.length - 1);
        nuc = qu[qu.length - 1];
    } else {
        // Non-Vietnamese word, return as-is
        return { ons: '', nuc: word, cod: '', ton: 1, isOOV: true };
    }

    // Extract tone from word
    for (let i = 0; i < l; i++) {
        if (word[i] in Cus_tones_p) {
            ton = Cus_tones_p[word[i]];
            break;
        }
    }

    // Velar Fronting (Northern dialect)
    // When coda is 'nh' (ɲ) and nucleus is 'a', change nucleus to 'ɛ'
    if (nuc === 'a' && cod === 'ɲ') {
        nuc = 'ɛ';
    }
    // When coda is 'ch' (from 'ach') and nucleus is 'a', change to 'ɛ' (for 'ch' ending)
    if (nuc === 'a' && cod === 'k' && cOffset === 2) {
        nuc = 'ɛ';
    }

    // Labialized allophony
    if (nuc in { 'u': 1, 'o': 1, 'ɔ': 1 }) {
        if (cod === 'ŋ') cod = 'ŋ͡m';
        if (cod === 'k') cod = 'k͡p';
    }

    return { ons, nuc, cod, ton };
}

/**
 * Convert a word to IPA string
 * @param {string} word 
 * @returns {string} IPA representation with tone
 */
function wordToIPA(word) {
    const { ons, nuc, cod, ton, isOOV } = trans(word);
    if (isOOV) {
        return '[' + word + ']';
    }
    return [ons, nuc, cod].filter(x => x).join('') + ton;
}


/**
 * Tokenize an IPA string into symbol IDs
 * Handles multi-character IPA symbols and diacritics
 * @param {string} ipa - IPA string to tokenize
 * @param {object} symbolToId - Symbol to ID mapping
 * @returns {number[]} - Array of symbol IDs
 */
function tokenizeIPA(ipa, symbolToId) {
    const tokens = [];
    let i = 0;

    while (i < ipa.length) {
        let matched = false;

        // Try matching longest possible substring first (up to 4 chars for symbols like 'ŋ͡m')
        for (let len = Math.min(4, ipa.length - i); len > 0; len--) {
            const substr = ipa.substring(i, i + len);
            if (symbolToId[substr] !== undefined) {
                tokens.push(symbolToId[substr]);
                i += len;
                matched = true;
                break;
            }
        }

        if (!matched) {
            // Fallback: try single character
            const ch = ipa[i];
            if (symbolToId[ch] !== undefined) {
                tokens.push(symbolToId[ch]);
            } else {
                // Use UNK for unknown symbols
                tokens.push(symbolToId['UNK'] || 305);
            }
            i++;
        }
    }

    return tokens;
}

/**
 * Check if character is a Unicode combining mark
 */
function isCombiningMark(char) {
    const code = char.charCodeAt(0);
    // Main combining diacritical marks range
    return (code >= 0x0300 && code <= 0x036F) ||
        // Additional combining marks
        (code >= 0x1AB0 && code <= 0x1AFF) ||
        (code >= 0x1DC0 && code <= 0x1DFF) ||
        (code >= 0x20D0 && code <= 0x20FF) ||
        (code >= 0xFE20 && code <= 0xFE2F);
}

/**
 * Convert Vietnamese text to IPA phonemes for TTS
 * @param {string} text - Vietnamese text
 * @param {object} symbolToId - Symbol to ID mapping
 * @param {number} viLangId - Vietnamese language ID
 * @returns {object} - {phonemes, tones, languages}
 */
function textToPhonemes(text, symbolToId, viLangId) {
    const phonemes = [];
    const tones = [];
    const languages = [];

    // viphoneme tone mapping: 1=ngang, 2=huyền, 3=ngã, 4=hỏi, 5=sắc, 6=nặng
    // Python internal: 0=ngang, 1=sắc, 2=huyền, 3=ngã, 4=hỏi, 5=nặng
    const VIPHONEME_TONE_MAP = { 1: 0, 2: 2, 3: 3, 4: 4, 5: 1, 6: 5 };

    const words = text.split(/\s+/);

    for (const word of words) {
        if (!word) continue;

        // Separate punctuation
        let cleanWord = word;
        const trailingPunct = [];

        // Remove trailing punctuation
        while (cleanWord && /[,.!?;:'"()\[\]{}]/.test(cleanWord[cleanWord.length - 1])) {
            trailingPunct.unshift(cleanWord[cleanWord.length - 1]);
            cleanWord = cleanWord.substring(0, cleanWord.length - 1);
        }

        // Process word
        if (cleanWord) {
            const { ons, nuc, cod, ton, isOOV } = trans(cleanWord);

            if (isOOV) {
                // OOV word - use UNK or pass through
                const id = symbolToId['UNK'] || 305;
                phonemes.push(id);
                tones.push(0); // tone 0 for OOV
                languages.push(viLangId);
            } else {
                // Combine IPA parts and tokenize char-by-char like Python
                const ipaStr = [ons, nuc, cod].filter(x => x).join('');

                // Map viphoneme tone (1-6) to internal tone (0-5)
                const internalTone = VIPHONEME_TONE_MAP[ton] || 0;

                // Tokenize character-by-character, matching Python phonemizer behavior
                const syllablePhones = [];
                let i = 0;

                while (i < ipaStr.length) {
                    const char = ipaStr[i];

                    // Skip combining marks (they modify previous char)
                    if (isCombiningMark(char)) {
                        i++;
                        continue;
                    }

                    // Modifier letters - append to previous phoneme if exists
                    if (char === 'ʷ' || char === 'ʰ' || char === 'ː') {
                        if (syllablePhones.length > 0) {
                            syllablePhones[syllablePhones.length - 1] += char;
                        }
                        i++;
                        continue;
                    }

                    // Tie bars - skip
                    if (char === '\u0361' || char === '\u035c') {
                        i++;
                        continue;
                    }

                    // Regular phoneme character
                    syllablePhones.push(char);
                    i++;
                }

                // Map to IDs
                for (const ph of syllablePhones) {
                    let id = symbolToId[ph];
                    if (id === undefined) {
                        // Use UNK for unknown symbols
                        id = symbolToId['UNK'] || 305;
                    }
                    phonemes.push(id);
                    tones.push(internalTone);
                    languages.push(viLangId);
                }
            }
        }

        // Add trailing punctuation
        for (const p of trailingPunct) {
            const id = symbolToId[p] !== undefined ? symbolToId[p] : symbolToId['UNK'] || 305;
            phonemes.push(id);
            tones.push(0);
            languages.push(viLangId);
        }
    }

    // Add boundary tokens at start and end (like Python phonemizer)
    const boundaryId = symbolToId['_'] || 0;
    phonemes.unshift(boundaryId);
    phonemes.push(boundaryId);
    tones.unshift(0);
    tones.push(0);
    languages.unshift(viLangId);
    languages.push(viLangId);

    // Add Vietnamese tone offset (like Python's cleaned_text_to_sequence)
    // VI tone_start = 16 (from language_tone_start_map)
    const VI_TONE_OFFSET = 16;
    const tonesWithOffset = tones.map(t => t + VI_TONE_OFFSET);

    return { phonemes, tones: tonesWithOffset, languages };
}

/**
 * Add blanks between phonemes (required for TTS model)
 */
function addBlanks(input, viLangId) {
    const { phonemes, tones, languages } = input;
    const withBlanks = [];
    const tonesWithBlanks = [];
    const langsWithBlanks = [];

    for (let i = 0; i < phonemes.length; i++) {
        withBlanks.push(0);
        tonesWithBlanks.push(0);
        langsWithBlanks.push(viLangId);

        withBlanks.push(phonemes[i]);
        tonesWithBlanks.push(tones[i]);
        langsWithBlanks.push(languages[i]);
    }

    withBlanks.push(0);
    tonesWithBlanks.push(0);
    langsWithBlanks.push(viLangId);

    return {
        phonemes: withBlanks,
        tones: tonesWithBlanks,
        languages: langsWithBlanks
    };
}

/**
 * Test function
 */
function testG2P() {
    const tests = [
        'xin', 'chào', 'Việt', 'Nam', 'tiếng', 'nói',
        'được', 'viết', 'người', 'trường', 'nghiệp'
    ];

    console.log('=== Vietnamese G2P Test ===');
    for (const word of tests) {
        const result = wordToIPA(word);
        console.log(`${word} -> ${result}`);
    }
}

// Export for browser
if (typeof window !== 'undefined') {
    window.VietnameseG2P = {
        textToPhonemes,
        addBlanks,
        wordToIPA,
        trans,
        testG2P
    };
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { textToPhonemes, addBlanks, wordToIPA, trans, testG2P };
}
