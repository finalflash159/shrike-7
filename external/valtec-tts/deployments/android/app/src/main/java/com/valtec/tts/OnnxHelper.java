package com.valtec.tts;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxTensorLike;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtSession;

import java.util.HashMap;
import java.util.Map;

/**
 * Java helper class to workaround Kotlin/ONNX type compatibility issues.
 */
public class OnnxHelper {

    /**
     * Run ONNX session with OnnxTensor inputs.
     */
    public static OrtSession.Result runWithTensors(OrtSession session, Map<String, OnnxTensor> inputs)
            throws Exception {
        // Convert to the expected type
        Map<String, OnnxTensorLike> tensorMap = new HashMap<>();
        for (Map.Entry<String, OnnxTensor> entry : inputs.entrySet()) {
            tensorMap.put(entry.getKey(), entry.getValue());
        }
        return session.run(tensorMap);
    }

    /**
     * Run ONNX session with OnnxValue inputs (for intermediate results).
     */
    public static OrtSession.Result runWithValues(OrtSession session, Map<String, OnnxValue> inputs)
            throws Exception {
        // OnnxValue includes OnnxTensor, need to cast appropriately
        Map<String, OnnxTensorLike> tensorMap = new HashMap<>();
        for (Map.Entry<String, OnnxValue> entry : inputs.entrySet()) {
            OnnxValue value = entry.getValue();
            if (value instanceof OnnxTensorLike) {
                tensorMap.put(entry.getKey(), (OnnxTensorLike) value);
            }
        }
        return session.run(tensorMap);
    }
}
